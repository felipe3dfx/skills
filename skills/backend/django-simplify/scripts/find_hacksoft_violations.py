"""Find HackSoft Django Styleguide violations.

Enforces the architectural patterns from the HackSoft Django Styleguide:
- Services must use keyword-only arguments (`*,`)
- Services that write must be wrapped in @transaction.atomic
- Model instances SHOULD call full_clean() before save() (advisory, low severity)
- Business logic belongs in services — not in views, forms, or serializers

Reference: https://github.com/HackSoftware/Django-Styleguide

Usage:
    python find_hacksoft_violations.py /path/to/project
    python find_hacksoft_violations.py . --min-severity high
    python find_hacksoft_violations.py . --format json
"""

import argparse
import ast
import json
import sys
from pathlib import Path

SKIP_DIRS = {
    '.venv',
    'venv',
    'env',
    '.env',
    'node_modules',
    '.git',
    'migrations',
    '__pycache__',
    'static',
    'media',
    'dist',
    'build',
    '.tox',
    'tests',
}

WRITE_VERBS = (
    'create',
    'update',
    'delete',
    'add',
    'remove',
    'assign',
    'issue',
    'cancel',
    'approve',
    'reject',
    'register',
    'bulk',
    'import',
    'sync',
    'publish',
    'archive',
)

NON_WRITE_PREFIXES = ('can_', 'is_', 'get_', 'has_', 'should_', 'to_', 'build_')

ORM_WRITE_CALLS = {
    'save',
    'create',
    'update',
    'delete',
    'bulk_create',
    'bulk_update',
    'get_or_create',
    'update_or_create',
}

VIEW_WRITE_METHODS = {
    'form_valid',
    'post',
    'put',
    'patch',
    'delete',
    'create',
    'update',
    'destroy',
    'perform_create',
    'perform_update',
    'perform_destroy',
}

FORM_WRITE_METHODS = {'save', 'clean'}

ORM_WRITE_METHODS = {'save', 'create', 'bulk_create', 'update', 'delete', 'bulk_update'}

SEVERITY_RANK = {'low': 0, 'medium': 1, 'high': 2}


def iter_python_files(root: Path):
    for path in root.rglob('*.py'):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def is_service_file(path: Path) -> bool:
    parts = path.parts
    if path.name == 'services.py':
        return True
    return 'services' in parts and path.suffix == '.py'


def is_view_file(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    return path.name in ('views.py', 'apis.py', 'viewsets.py') or any(
        p in parts for p in ('views', 'apis', 'viewsets')
    )


def has_decorator(node: ast.FunctionDef, needle: str) -> bool:
    for dec in node.decorator_list:
        try:
            if needle in ast.unparse(dec):
                return True
        except AttributeError, ValueError:
            continue
    return False


def looks_like_write(func_name: str) -> bool:
    lower = func_name.lower()
    return any(verb in lower for verb in WRITE_VERBS)


def _has_orm_write_in_body(func: ast.FunctionDef) -> bool:
    """Return True if the function body contains an ORM write call.

    Looks for `.save()`, `.create()`, `.update()`, `.delete()`,
    `.bulk_create()`, `.bulk_update()`, `.get_or_create()`,
    `.update_or_create()` on any attribute target.
    """
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr in ORM_WRITE_CALLS:
            return True
    return False


# ---------------------------------------------------------------------------
# Rule 1: service functions must be keyword-only
# ---------------------------------------------------------------------------

DJANGO_FRAMEWORK_OVERRIDES = {
    'authenticate',
    'get_user',
    'get_username',
    'get_by_natural_key',
    'has_perm',
    'has_module_perms',
    'get_all_permissions',
    'get_group_permissions',
    'configure_user',
    'clean_username',
}


def check_service_kwargs_only(func: ast.FunctionDef, path: Path):
    if func.name.startswith('_'):
        return
    if func.name in DJANGO_FRAMEWORK_OVERRIDES:
        return
    args = func.args
    has_positional = bool(args.args or args.posonlyargs)
    has_star_separator = args.vararg is not None or bool(args.kwonlyargs)
    if has_positional and not has_star_separator:
        yield {
            'file': str(path),
            'line': func.lineno,
            'severity': 'medium',
            'issue': (
                f"Service '{func.name}' uses positional args (HackSoft: require `*,` keyword-only)"
            ),
        }


# ---------------------------------------------------------------------------
# Rule 2: write-like services must be @transaction.atomic
# ---------------------------------------------------------------------------


def check_service_transaction_atomic(func: ast.FunctionDef, path: Path):
    if func.name.startswith('_') or not looks_like_write(func.name):
        return
    if any(func.name.lower().startswith(p) for p in NON_WRITE_PREFIXES):
        return
    if not _has_orm_write_in_body(func):
        return
    if has_decorator(func, 'transaction.atomic') or has_decorator(func, '@atomic'):
        return
    # Also accept `with transaction.atomic():` as the outermost statement
    if func.body and isinstance(func.body[0], ast.With):
        src = ast.unparse(func.body[0].items[0].context_expr) if func.body[0].items else ''
        if 'atomic' in src:
            return
    yield {
        'file': str(path),
        'line': func.lineno,
        'severity': 'high',
        'issue': (
            f"Service '{func.name}' looks like a write but is not wrapped in @transaction.atomic"
        ),
    }


# ---------------------------------------------------------------------------
# Rule 3: save() without preceding full_clean()
# ---------------------------------------------------------------------------


def check_save_without_full_clean(tree: ast.AST, path: Path):
    for parent in ast.walk(tree):
        body = getattr(parent, 'body', None)
        if not isinstance(body, list):
            continue
        for i, stmt in enumerate(body):
            call = _extract_save_call(stmt)
            if call is None:
                continue
            target = call.func.value
            if not isinstance(target, ast.Name):
                continue
            if target.id in ('self', 'super', 'cls'):
                continue
            if _cleaned_before(body, i, target.id):
                continue
            yield {
                'file': str(path),
                'line': stmt.lineno,
                'severity': 'low',
                'issue': (
                    f"'{target.id}.save()' called without prior "
                    f"'{target.id}.full_clean()' "
                    '(advisory — review if this is a Django model)'
                ),
            }


def _extract_save_call(stmt: ast.stmt) -> ast.Call | None:
    is_expr_call = isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
    is_assign_call = isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call)
    if is_expr_call or is_assign_call:
        call = stmt.value
    else:
        return None
    if isinstance(call.func, ast.Attribute) and call.func.attr == 'save':
        return call
    return None


def _cleaned_before(body: list, index: int, var_name: str) -> bool:
    needle = f'{var_name}.full_clean'
    for prev in body[:index]:
        try:
            if needle in ast.unparse(prev):
                return True
        except AttributeError, ValueError:
            continue
    return False


# ---------------------------------------------------------------------------
# Rule 4: business logic in views
# ---------------------------------------------------------------------------


def check_business_logic_in_view(func: ast.FunctionDef, path: Path):
    if func.name not in VIEW_WRITE_METHODS:
        return
    # Size gate: ignore short methods even if score is high
    end = getattr(func, 'end_lineno', func.lineno)
    if end - func.lineno < 15:
        return
    score = 0
    for sub in ast.walk(func):
        if isinstance(sub, (ast.For, ast.While, ast.If)):
            score += 1
        elif (
            isinstance(sub, ast.Call)
            and isinstance(sub.func, ast.Attribute)
            and sub.func.attr in ORM_WRITE_METHODS
        ):
            base = sub.func.value
            if isinstance(base, ast.Name) and base.id not in ('self', 'super', 'cls'):
                score += 3
    if score >= 6:
        yield {
            'file': str(path),
            'line': func.lineno,
            'severity': 'medium',
            'issue': f"View method '{func.name}' contains business logic — delegate to services.py",
        }


# ---------------------------------------------------------------------------
# Rule 5: business logic in Forms / Serializers
# ---------------------------------------------------------------------------


def class_inherits(cls: ast.ClassDef, *needles: str) -> bool:
    for base in cls.bases:
        try:
            src = ast.unparse(base)
        except AttributeError, ValueError:
            continue
        if any(needle in src for needle in needles):
            return True
    return False


def check_business_logic_in_form_or_serializer(cls: ast.ClassDef, path: Path):
    is_form = class_inherits(cls, 'Form')
    is_serializer = class_inherits(cls, 'Serializer')
    if not (is_form or is_serializer):
        return
    kind = 'Form' if is_form else 'Serializer'
    target_methods = FORM_WRITE_METHODS if is_form else {'create', 'update', 'save'}
    for node in cls.body:
        if not isinstance(node, ast.FunctionDef) or node.name not in target_methods:
            continue
        for sub in ast.walk(node):
            if not (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)):
                continue
            if sub.func.attr in ORM_WRITE_METHODS:
                base = sub.func.value
                if isinstance(base, ast.Name) and base.id in ('self', 'super', 'cls'):
                    continue
                yield {
                    'file': str(path),
                    'line': sub.lineno,
                    'severity': 'medium',
                    'issue': (
                        f"{kind} '{cls.name}.{node.name}()' performs ORM write "
                        '— move to services.py'
                    ),
                }
                break


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def scan_file(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except SyntaxError, UnicodeDecodeError, OSError:
        return

    in_service = is_service_file(path)
    in_view = is_view_file(path)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if in_service:
                yield from check_service_kwargs_only(node, path)
                yield from check_service_transaction_atomic(node, path)
            if in_view:
                yield from check_business_logic_in_view(node, path)
        elif isinstance(node, ast.ClassDef):
            yield from check_business_logic_in_form_or_serializer(node, path)

    if in_service:
        yield from check_save_without_full_clean(tree, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    parser.add_argument('--min-severity', choices=('low', 'medium', 'high'), default='low')
    args = parser.parse_args()

    threshold = SEVERITY_RANK[args.min_severity]
    root = args.path.resolve()

    findings = []
    for path in iter_python_files(root):
        findings.extend(
            finding
            for finding in scan_file(path)
            if SEVERITY_RANK[finding['severity']] >= threshold
        )

    if args.format == 'json':
        json.dump(findings, sys.stdout, indent=2)
        sys.stdout.write('\n')
        return 1 if findings else 0

    if not findings:
        print('No HackSoft styleguide violations detected.')
        return 0

    grouped: dict[str, list[dict]] = {'high': [], 'medium': [], 'low': []}
    for f in findings:
        grouped[f['severity']].append(f)

    for sev in ('high', 'medium', 'low'):
        items = grouped[sev]
        if not items:
            continue
        print(f'\n=== {sev.upper()} ({len(items)}) ===')
        for f in items:
            print(f'  {f["file"]}:{f["line"]}')
            print(f'      {f["issue"]}')

    print(f'\nTotal: {len(findings)} violations')
    return 1


if __name__ == '__main__':
    sys.exit(main())

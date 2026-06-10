"""Find Django model safety issues.

Detects structural problems in Django models that cause data corruption,
inconsistent pagination, or schema drift.

Rules:
    R1 (high)   on_delete=CASCADE on any FK — review case by case.
    R2 (medium) null=True on CharField / TextField — Django anti-pattern
                (use '' instead so you don't have two empty states).
    R3 (medium) CharField / TextField without explicit max_length.
    R4 (high)   DecimalField without max_digits or decimal_places.
    R5 (low)    Concrete models without Meta.ordering — paginated views
                will have non-deterministic ordering.

Usage:
    python find_model_safety.py /path/to/project
    python find_model_safety.py . --min-severity high
    python find_model_safety.py . --format json
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

SEVERITY_RANK = {'low': 0, 'medium': 1, 'high': 2}


def iter_python_files(root: Path):
    for path in root.rglob('*.py'):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def is_model_file(path: Path) -> bool:
    if path.name == 'models.py':
        return True
    return 'models' in path.parts and path.suffix == '.py'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def field_call_name(call: ast.Call) -> str | None:
    """Return the field class name: ForeignKey / CharField / DecimalField ..."""
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def get_kwarg(call: ast.Call, name: str) -> ast.expr | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def inherits_model(cls: ast.ClassDef) -> bool:
    for base in cls.bases:
        try:
            src = ast.unparse(base)
        except AttributeError, ValueError:
            continue
        if 'Model' in src:
            return True
    return False


def is_abstract_model(cls: ast.ClassDef) -> bool:
    for node in cls.body:
        if isinstance(node, ast.ClassDef) and node.name == 'Meta':
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for tgt in stmt.targets:
                        if (
                            isinstance(tgt, ast.Name)
                            and tgt.id == 'abstract'
                            and isinstance(stmt.value, ast.Constant)
                            and stmt.value.value is True
                        ):
                            return True
    return False


def meta_has_ordering(cls: ast.ClassDef) -> bool:
    for node in cls.body:
        if isinstance(node, ast.ClassDef) and node.name == 'Meta':
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for tgt in stmt.targets:
                        if isinstance(tgt, ast.Name) and tgt.id == 'ordering':
                            return True
    return False


def fk_target_name(call: ast.Call) -> str | None:
    """For ForeignKey('Customer', ...) or ForeignKey(Customer, ...) or
    ForeignKey('app.Customer', ...), return the model name.
    """
    if not call.args:
        return None
    first = call.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        raw = first.value
        return raw.split('.')[-1]  # 'app.Customer' -> 'Customer'
    if isinstance(first, ast.Name):
        return first.id
    if isinstance(first, ast.Attribute):
        return first.attr
    return None


# ---------------------------------------------------------------------------
# Rule checks
# ---------------------------------------------------------------------------


def check_field(call: ast.Call, field_name: str, path: Path):
    kind = field_call_name(call)
    if kind is None:
        return

    # R1: CASCADE on any FK — review case by case
    if kind in ('ForeignKey', 'OneToOneField'):
        on_delete = get_kwarg(call, 'on_delete')
        target = fk_target_name(call) or '?'
        if on_delete is not None:
            try:
                src = ast.unparse(on_delete)
            except AttributeError, ValueError:
                src = ''
            if 'CASCADE' in src:
                yield {
                    'file': str(path),
                    'line': call.lineno,
                    'severity': 'high',
                    'issue': (
                        f"FK '{field_name}' -> {target} uses on_delete=CASCADE "
                        f'— review if cascade delete is intentional (consider PROTECT/SET_NULL)'
                    ),
                }

    # R2 & R3: CharField / TextField
    if kind in ('CharField', 'TextField'):
        null_kw = get_kwarg(call, 'null')
        if isinstance(null_kw, ast.Constant) and null_kw.value is True:
            yield {
                'file': str(path),
                'line': call.lineno,
                'severity': 'medium',
                'issue': (
                    f"'{field_name}' is {kind}(null=True) — "
                    f"Django anti-pattern, use default='' instead"
                ),
            }
        if kind == 'CharField' and get_kwarg(call, 'max_length') is None:
            yield {
                'file': str(path),
                'line': call.lineno,
                'severity': 'medium',
                'issue': f"CharField '{field_name}' missing max_length",
            }

    # R4: DecimalField
    if kind == 'DecimalField' and (
        get_kwarg(call, 'max_digits') is None or get_kwarg(call, 'decimal_places') is None
    ):
        yield {
            'file': str(path),
            'line': call.lineno,
            'severity': 'high',
            'issue': (f"DecimalField '{field_name}' missing max_digits or decimal_places"),
        }


def check_class(cls: ast.ClassDef, path: Path):
    if not inherits_model(cls):
        return
    if is_abstract_model(cls):
        return

    # Iterate field assignments at class level
    for stmt in cls.body:
        if not isinstance(stmt, ast.Assign) or not isinstance(stmt.value, ast.Call):
            continue
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            continue
        field_name = stmt.targets[0].id
        yield from check_field(stmt.value, field_name, path)

    # R5: Missing Meta.ordering
    if not meta_has_ordering(cls):
        yield {
            'file': str(path),
            'line': cls.lineno,
            'severity': 'low',
            'issue': (
                f"Model '{cls.name}' has no Meta.ordering — "
                f'paginated queries will be non-deterministic'
            ),
        }


def scan_file(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except SyntaxError, UnicodeDecodeError, OSError:
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            yield from check_class(node, path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    parser.add_argument('--min-severity', choices=('low', 'medium', 'high'), default='low')
    args = parser.parse_args()

    threshold = SEVERITY_RANK[args.min_severity]
    root = args.path.resolve()

    print('Scanning for model safety issues in models.py files.', file=sys.stderr)

    findings = []
    for path in iter_python_files(root):
        if not is_model_file(path):
            continue
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
        print('No model safety issues detected.')
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

    print(f'\nTotal: {len(findings)} findings')
    return 1


if __name__ == '__main__':
    sys.exit(main())

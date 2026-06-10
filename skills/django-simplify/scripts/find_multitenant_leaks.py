"""Find multi-tenant data leaks in Django views, APIs, and selectors.

Detects queries that do NOT filter by the project's tenant field
(e.g. customer, organization, workspace) in customer-aware contexts.

Configuration (resolved in this order):
1. CLI flag: --tenant-field <name>
2. pyproject.toml in project root, [tool.django-simplify.tenant] field = "..."
3. django-simplify.toml in project root, [tenant] field = "..." (legacy)
4. Auto-detection: scans models for FKs named after common tenant candidates
5. If none found, the script exits silently (project is not multi-tenant)

Shared models allowlist:
Reference / catalog models that are global (not per-tenant) should be added
to pyproject.toml under [tool.django-simplify.tenant] shared_models = [...].
Queries on allowlisted models are never flagged. Example:

    [tool.django-simplify.tenant]
    field = "customer"
    shared_models = ["Country", "State", "City", "Currency"]

Scope of detection:
Only calls inside function or method bodies are flagged. Module-level and
class-level assignments (e.g. DRF `queryset = Model.objects.all()` class
attribute) are ignored because the real filtering typically happens in an
overridden `get_queryset()`.

Usage:
    python find_multitenant_leaks.py /path/to/project
    python find_multitenant_leaks.py . --tenant-field organization
    python find_multitenant_leaks.py . --format json
"""

import argparse
import ast
import json
import sys
import tomllib
from collections import Counter
from pathlib import Path

NON_MODEL_ROOTS = ('self', 'cls', 'request', 'super')

TENANT_CANDIDATES = (
    'customer',
    'tenant',
    'organization',
    'org',
    'workspace',
    'account',
    'client',
    'company',
    'owner',
)

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
}

TARGET_FILE_TAGS = ('view', 'api', 'selector', 'viewset')

QUERYSET_METHODS = {'filter', 'all', 'get', 'first', 'last', 'exclude', 'exists', 'count'}


def iter_python_files(root: Path):
    for path in root.rglob('*.py'):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def load_tenant_field(root: Path, cli_override: str | None) -> str | None:
    if cli_override:
        return cli_override
    # 1. pyproject.toml under [tool.django-simplify.tenant]
    field = _read_toml_value(
        root / 'pyproject.toml',
        ('tool', 'django-simplify', 'tenant', 'field'),
    )
    if isinstance(field, str):
        return field
    # 2. legacy standalone django-simplify.toml
    field = _read_toml_value(
        root / 'django-simplify.toml',
        ('tenant', 'field'),
    )
    if isinstance(field, str):
        return field
    return autodetect_tenant_field(root)


def load_shared_models(root: Path) -> frozenset[str]:
    """Load allowlist of reference/catalog models that are not tenant-scoped."""
    value = _read_toml_value(
        root / 'pyproject.toml',
        ('tool', 'django-simplify', 'tenant', 'shared_models'),
    )
    if isinstance(value, list):
        return frozenset(str(m) for m in value)
    value = _read_toml_value(
        root / 'django-simplify.toml',
        ('tenant', 'shared_models'),
    )
    if isinstance(value, list):
        return frozenset(str(m) for m in value)
    return frozenset()


def _read_toml_value(path: Path, key_path: tuple[str, ...]):
    if not path.exists():
        return None
    try:
        with path.open('rb') as fh:
            data = tomllib.load(fh)
    except tomllib.TOMLDecodeError, OSError:
        return None
    cursor: object = data
    for key in key_path:
        if not isinstance(cursor, dict) or key not in cursor:
            return None
        cursor = cursor[key]
    return cursor


def autodetect_tenant_field(root: Path) -> str | None:
    counter: Counter[str] = Counter()
    for path in iter_python_files(root):
        if path.name != 'models.py' and 'models' not in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
        except SyntaxError, UnicodeDecodeError, OSError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
                continue
            func = node.value.func
            fname = getattr(func, 'attr', None) or getattr(func, 'id', None)
            if fname not in ('ForeignKey', 'OneToOneField'):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in TENANT_CANDIDATES:
                    counter[target.id] += 1
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def is_target_file(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    if any(tag in parts for tag in ('views', 'apis', 'selectors', 'viewsets')):
        return True
    stem = path.stem.lower()
    return any(tag in stem for tag in TARGET_FILE_TAGS)


def call_mentions_tenant(call: ast.Call, tenant_field: str) -> bool:
    try:
        src = ast.unparse(call)
    except AttributeError, ValueError:
        return False
    return tenant_field in src


def is_queryset_call(node: ast.Call) -> str | None:
    if not isinstance(node.func, ast.Attribute):
        return None
    if node.func.attr in QUERYSET_METHODS:
        return node.func.attr
    return None


def is_get_object_or_404(node: ast.Call) -> bool:
    return isinstance(node.func, ast.Name) and node.func.id == 'get_object_or_404'


def extract_model_name(call: ast.Call) -> str | None:
    """For Model.objects.method(...) or models.Model.objects.method(...),
    return the model class name ('Model').
    """
    current: ast.AST = call.func
    while isinstance(current, ast.Attribute):
        if current.attr == 'objects':
            parent = current.value
            if isinstance(parent, ast.Name):
                return parent.id
            if isinstance(parent, ast.Attribute):
                return parent.attr
            return None
        current = current.value
    return None


def chain_starts_with_model_objects(call: ast.Call) -> bool:
    """Detect chains like `Model.objects.method(...)` or `models.Model.objects.method(...)`.

    Rejects chains rooted in `self`, `request`, `cls`, etc., because those
    usually go through a pre-filtered queryset (e.g. `self.get_queryset()`).
    """
    current: ast.AST = call.func
    while isinstance(current, ast.Attribute):
        if current.attr == 'objects':
            parent = current.value
            if isinstance(parent, ast.Name):
                return parent.id not in NON_MODEL_ROOTS
            if isinstance(parent, ast.Attribute):
                # models.Invoice.objects.X — walk to the root to reject self.foo.objects
                root: ast.AST = parent
                while isinstance(root, ast.Attribute):
                    root = root.value
                return isinstance(root, ast.Name) and root.id not in NON_MODEL_ROOTS
            return False
        current = current.value
    return False


def extract_first_arg_model(call: ast.Call) -> str | None:
    """For get_object_or_404(Model, ...) or (models.Model, ...) return the name."""
    if not call.args:
        return None
    first = call.args[0]
    if isinstance(first, ast.Name):
        return first.id
    if isinstance(first, ast.Attribute):
        return first.attr
    return None


class LeakVisitor(ast.NodeVisitor):
    """Walks an AST and flags tenant-missing queries INSIDE function bodies only.

    Class-level assignments (e.g. DRF `queryset = Model.objects.all()`) are
    ignored because the real filtering usually lives in an overridden
    `get_queryset()` method.
    """

    def __init__(self, path: Path, tenant_field: str, shared_models: frozenset[str]) -> None:
        self.path = path
        self.tenant_field = tenant_field
        self.shared_models = shared_models
        self.function_depth = 0
        self.findings: list[dict] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def visit_Call(self, node: ast.Call) -> None:
        if self.function_depth > 0:
            self._check_call(node)
        self.generic_visit(node)

    def _check_call(self, node: ast.Call) -> None:
        if is_get_object_or_404(node):
            # Skip if the first arg is a pre-filtered queryset call:
            #   get_object_or_404(Model.objects.filter(...), ...)
            #   get_object_or_404(qs.for_user(user), ...)
            # The filtering already happened upstream.
            if node.args and isinstance(node.args[0], ast.Call):
                return
            model = extract_first_arg_model(node)
            if model and model in self.shared_models:
                return
            if call_mentions_tenant(node, self.tenant_field):
                return
            self.findings.append({
                'file': str(self.path),
                'line': node.lineno,
                'severity': 'high',
                'issue': (
                    f'get_object_or_404({model or "?"}, ...) '
                    f'without {self.tenant_field} ownership check'
                ),
            })
            return

        method = is_queryset_call(node)
        if not method or not chain_starts_with_model_objects(node):
            return
        model = extract_model_name(node)
        if model and model in self.shared_models:
            return
        if call_mentions_tenant(node, self.tenant_field):
            return
        self.findings.append({
            'file': str(self.path),
            'line': node.lineno,
            'severity': 'high',
            'issue': f'{model or "Model"}.objects.{method}(...) without {self.tenant_field} filter',
        })


def find_leaks_in_file(path: Path, tenant_field: str, shared_models: frozenset[str]):
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except SyntaxError, UnicodeDecodeError, OSError:
        return
    visitor = LeakVisitor(path, tenant_field, shared_models)
    visitor.visit(tree)
    yield from visitor.findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--tenant-field', default=None)
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    args = parser.parse_args()

    root = args.path.resolve()
    tenant_field = load_tenant_field(root, args.tenant_field)
    if not tenant_field:
        print(
            'No tenant field detected or configured. Project is not multi-tenant. Skipping.',
            file=sys.stderr,
        )
        return 0

    shared_models = load_shared_models(root)
    print(
        f'Scanning for multi-tenant leaks using field: {tenant_field!r} '
        f'(shared models allowlist: {len(shared_models)})',
        file=sys.stderr,
    )

    findings = []
    for path in iter_python_files(root):
        if not is_target_file(path):
            continue
        findings.extend(find_leaks_in_file(path, tenant_field, shared_models))

    if args.format == 'json':
        json.dump(findings, sys.stdout, indent=2)
        sys.stdout.write('\n')
    elif not findings:
        print('No multi-tenant leaks detected.')
    else:
        print(f'\nFound {len(findings)} potential multi-tenant leaks:\n')
        for f in findings:
            print(f'  [{f["severity"].upper()}] {f["file"]}:{f["line"]}')
            print(f'      {f["issue"]}')

    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())

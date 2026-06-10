"""Find pytest-django convention violations in a Django project.

Enforces the project conventions documented in SKILL.md:

    R1 (high)   Test file named 'test_*.py' — convention is '*_tests.py'.
    R2 (high)   Class-based test — convention is function-based tests only.
    R3 (high)   'Model.objects.create(...)' inside a test function — tests
                must use Factory Boy factories via pytest_factoryboy.
    R4 (high)   'mocker.patch('apps.…')' — mocking internal project code.
                Mocks must be at the HTTP / network boundary
                (e.g. 'requests.Session.request').

Usage:
    python find_pytest_violations.py /path/to/project
    python find_pytest_violations.py . --format json
    python find_pytest_violations.py . --min-severity high
"""

import argparse
import ast
import json
import re
import sys
import tomllib
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
}

SEVERITY_RANK = {'low': 0, 'medium': 1, 'high': 2}


def iter_test_files(root: Path):
    """Yield Python files that look like test modules."""
    for path in root.rglob('*.py'):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        name = path.name
        if name.endswith('_tests.py') or name.startswith('test_'):
            yield path


# ---------------------------------------------------------------------------
# R1: misnamed test file
# ---------------------------------------------------------------------------

TEST_UTIL_FILENAMES = {'test_utils.py', 'test_helpers.py'}


def check_filename(path: Path):
    if path.name in TEST_UTIL_FILENAMES:
        return
    if path.name.startswith('test_') and not path.name.endswith('_tests.py'):
        yield {
            'file': str(path),
            'line': 1,
            'severity': 'high',
            'issue': (
                f"Test file '{path.name}' uses 'test_*.py' naming — convention is '*_tests.py'"
            ),
        }


# ---------------------------------------------------------------------------
# R2: class-based tests
# ---------------------------------------------------------------------------


def check_class_based_tests(tree: ast.AST, path: Path):
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if not isinstance(node, ast.ClassDef):
            continue
        # Only flag classes that look like test containers
        if node.name.startswith('Test') or any(
            isinstance(b, ast.Name) and b.id.endswith('TestCase') for b in node.bases
        ):
            yield {
                'file': str(path),
                'line': node.lineno,
                'severity': 'high',
                'issue': (
                    f"Class-based test '{node.name}' — convention is function-based tests only"
                ),
            }


# ---------------------------------------------------------------------------
# R3: Model.objects.create() in tests
# ---------------------------------------------------------------------------


def _is_objects_create(call: ast.Call) -> bool:
    func = call.func
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr not in ('create', 'bulk_create', 'update_or_create', 'get_or_create'):
        return False
    # func.value should be Attribute(attr='objects', value=Name(Model))
    parent = func.value
    if not isinstance(parent, ast.Attribute) or parent.attr != 'objects':
        return False
    root = parent.value
    # Only flag when the chain root is a Name (Model class), not self/cls/request
    if isinstance(root, ast.Name):
        return root.id not in ('self', 'cls', 'super', 'request')
    if isinstance(root, ast.Attribute):
        # models.Foo.objects.create(...) — walk to the root
        cursor: ast.AST = root
        while isinstance(cursor, ast.Attribute):
            cursor = cursor.value
        return isinstance(cursor, ast.Name) and cursor.id not in (
            'self',
            'cls',
            'super',
            'request',
        )
    return False


def _extract_model_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Attribute):
        parent = func.value
        if isinstance(parent, ast.Attribute) and parent.attr == 'objects':
            base = parent.value
            if isinstance(base, ast.Name):
                return base.id
            if isinstance(base, ast.Attribute):
                return base.attr
    return '?'


def check_model_objects_create(tree: ast.AST, path: Path):
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith('test_'):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and _is_objects_create(sub):
                model = _extract_model_name(sub)
                method = sub.func.attr if isinstance(sub.func, ast.Attribute) else '?'
                yield {
                    'file': str(path),
                    'line': sub.lineno,
                    'severity': 'high',
                    'issue': (
                        f"Test '{node.name}' uses {model}.objects.{method}(...) — "
                        f'use a Factory Boy factory instead'
                    ),
                }


# ---------------------------------------------------------------------------
# R4: mocker.patch('apps.…')
# ---------------------------------------------------------------------------


def _is_mocker_patch(call: ast.Call) -> bool:
    func = call.func
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr not in ('patch', 'patch_object'):
        return False
    base = func.value
    if isinstance(base, ast.Name) and base.id in ('mocker', 'mock'):
        return True
    # mocker.patch.object(...)
    if isinstance(base, ast.Attribute) and base.attr == 'patch':
        inner = base.value
        if isinstance(inner, ast.Name) and inner.id in ('mocker', 'mock'):
            return True
    return False


# Django / stdlib short-name callables that are re-exported at project import
# sites. There is no way to derive these from pyproject.toml because the name
# used inside project code ('render', not 'django.shortcuts.render') doesn't
# carry the package name.
FRAMEWORK_TERMINAL_NAMES = frozenset({
    # Django shortcuts / mail
    'render',
    'redirect',
    'reverse',
    'send_mail',
    'EmailMessage',
    'get_connection',
    'get_template',
    'TemplateResponse',
    # stdlib datetime
    'now',
    'localtime',
    'datetime',
    'date',
    'timedelta',
    # stdlib stat module helpers (patched at import site)
    'S_ISREG',
    'S_ISDIR',
    'S_ISLNK',
    'S_ISFIFO',
    'S_ISSOCK',
    # stdlib builtins
    'open',
    'print',
    'input',
    # Logger instances — mocking loggers for assertion is a legitimate pattern
    'logger',
    'log',
    'LOGGER',
    'LOG',
})

_DEP_NAME_RE = re.compile(r'^([A-Za-z0-9_.\-]+)')


def load_external_libs(root: Path) -> frozenset[str]:
    """Extract package names from pyproject.toml to use as external-lib
    segments for mocker.patch paths. Returns a frozenset of candidate
    import-name segments for every declared dependency (main + dev).
    """
    pyproject = root / 'pyproject.toml'
    if not pyproject.exists():
        return frozenset()
    try:
        with pyproject.open('rb') as fh:
            data = tomllib.load(fh)
    except tomllib.TOMLDecodeError, OSError:
        return frozenset()

    raw: list[str] = []
    project = data.get('project', {}) if isinstance(data.get('project'), dict) else {}
    deps = project.get('dependencies', [])
    if isinstance(deps, list):
        raw.extend(d for d in deps if isinstance(d, str))
    groups_data = data.get('dependency-groups')
    groups = groups_data if isinstance(groups_data, dict) else {}
    for val in groups.values():
        if isinstance(val, list):
            raw.extend(d for d in val if isinstance(d, str))

    segments: set[str] = set()
    for spec in raw:
        m = _DEP_NAME_RE.match(spec.strip())
        if not m:
            continue
        name = m.group(1).lower()
        # Canonical name with underscores (PyPI normalization for imports)
        underscored = name.replace('-', '_')
        segments.add(underscored)
        # Also add the trailing part after common prefixes so 'django-storages'
        # matches the 'storages' import, 'pytest-django' matches 'pytest_django'
        # but also its submodules.
        for prefix in ('django_', 'pytest_', 'python_', 'py_'):
            if underscored.startswith(prefix):
                stripped = underscored[len(prefix) :]
                if stripped:
                    segments.add(stripped)
    return frozenset(segments)


def _is_legitimate_external_patch(target: str, external_libs: frozenset[str]) -> bool:
    """True if the mocker.patch target is an external lib or framework builtin
    patched at its import site (canonical Python mock pattern).
    """
    segments = target.split('.')
    if segments and segments[-1] in FRAMEWORK_TERMINAL_NAMES:
        return True
    # If any middle segment matches a declared dependency, this is patching
    # that lib at its import site within project code — legitimate.
    # Start from index 2 to skip 'apps.<app>'.
    return any(seg.lower() in external_libs for seg in segments[2:])


def check_internal_mocks(tree: ast.AST, path: Path, external_libs: frozenset[str]):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_mocker_patch(node):
            continue
        if not node.args:
            continue
        first = node.args[0]
        if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
            continue
        target = first.value
        if not target.startswith('apps.'):
            continue
        if _is_legitimate_external_patch(target, external_libs):
            continue
        if True:
            yield {
                'file': str(path),
                'line': node.lineno,
                'severity': 'high',
                'issue': (
                    f"mocker.patch('{target}') mocks internal project code — "
                    f'mock at HTTP boundary (requests.Session.request) instead'
                ),
            }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def scan_file(path: Path, external_libs: frozenset[str]):
    yield from check_filename(path)
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except SyntaxError, UnicodeDecodeError, OSError:
        return
    yield from check_class_based_tests(tree, path)
    yield from check_model_objects_create(tree, path)
    yield from check_internal_mocks(tree, path, external_libs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    parser.add_argument('--min-severity', choices=('low', 'medium', 'high'), default='low')
    args = parser.parse_args()

    threshold = SEVERITY_RANK[args.min_severity]
    root = args.path.resolve()
    external_libs = load_external_libs(root)

    print(
        f'Scanning for pytest-django convention violations '
        f'({len(external_libs)} external libs detected from pyproject.toml).',
        file=sys.stderr,
    )

    findings = []
    for path in iter_test_files(root):
        findings.extend(
            finding
            for finding in scan_file(path, external_libs)
            if SEVERITY_RANK[finding['severity']] >= threshold
        )

    if args.format == 'json':
        json.dump(findings, sys.stdout, indent=2)
        sys.stdout.write('\n')
        return 1 if findings else 0

    if not findings:
        print('No pytest convention violations detected.')
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

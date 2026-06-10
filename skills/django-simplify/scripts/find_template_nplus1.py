"""Find N+1 query candidates in Django templates.

Scans .html templates for loops that access attributes on the loop variable
in ways that typically trigger N+1 queries at render time. These are hints,
not confirmed bugs — the view may already pre-fetch the data with
select_related / prefetch_related. Use the findings as a starting point
for investigation.

Rules:
    R1 (medium) Loop var traversed across 2+ FK hops:
                  {% for obj in qs %}{{ obj.customer.name }}{% endfor %}
                Candidate for select_related('customer').

    R2 (medium) Loop var accessing a reverse manager method:
                  {% for obj in qs %}{{ obj.items.count }}{% endfor %}
                Candidate for prefetch_related('items') + Count() annotation.

Limitation:
    This script is regex-based and has NO knowledge of the view that rendered
    the template, so it cannot tell whether select_related was already applied.
    Treat output as a checklist, not as ground truth.

Usage:
    python find_template_nplus1.py /path/to/project
    python find_template_nplus1.py . --format json
"""

import argparse
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    '.venv',
    'venv',
    'env',
    '.env',
    'node_modules',
    '.git',
    '__pycache__',
    'static',
    'media',
    'dist',
    'build',
    '.tox',
}

SEVERITY_RANK = {'low': 0, 'medium': 1, 'high': 2}

# {% for X in Y %} ... {% endfor %} — non-greedy, allows nesting via stack below
FOR_OPEN_RE = re.compile(r'{%\s*for\s+([a-zA-Z_]\w*)\s+in\s+[^%]+%}')
FOR_CLOSE_RE = re.compile(r'{%\s*endfor\s*%}')

# {{ var.attr.attr ... }} — capture the full dotted chain
VAR_RE = re.compile(r'{{\s*([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)+)[\s|}]')

# Reverse manager / queryset-ish terminal accessors that typically hit the DB
MANAGER_METHODS = {'all', 'count', 'first', 'last', 'exists', 'filter'}

# Loop-local variables that should never be treated as an FK chain
LOOP_LOCALS = {'forloop'}

# Attributes that are cheap and should NOT count as FK hops
SAFE_ATTRS = {
    'id',
    'pk',
    'name',
    'title',
    'slug',
    'value',
    'label',
    'created_at',
    'updated_at',
    'modified_at',
    'is_active',
    'is_deleted',
    'is_staff',
    'is_superuser',
    'first',
    'last',  # common iterator state, not FK
}


def iter_template_files(root: Path):
    for path in root.rglob('*.html'):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def find_for_scopes(text: str) -> list[tuple[int, int, str]]:
    """Return list of (start_offset, end_offset, loop_var) for every for block.

    Supports nesting: scopes cover the full body of their loop.
    """
    scopes: list[tuple[int, int, str]] = []
    stack: list[tuple[int, str]] = []
    pos = 0
    while pos < len(text):
        m_open = FOR_OPEN_RE.search(text, pos)
        m_close = FOR_CLOSE_RE.search(text, pos)
        if m_open and (not m_close or m_open.start() < m_close.start()):
            stack.append((m_open.end(), m_open.group(1)))
            pos = m_open.end()
        elif m_close:
            if stack:
                start, var = stack.pop()
                scopes.append((start, m_close.start(), var))
            pos = m_close.end()
        else:
            break
    return scopes


def line_number(text: str, offset: int) -> int:
    return text.count('\n', 0, offset) + 1


def analyze_chain(chain: str) -> tuple[str, list[str]]:
    """'obj.customer.name' -> ('obj', ['customer', 'name'])."""
    parts = chain.split('.')
    return parts[0], parts[1:]


def scan_template(path: Path):
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError, OSError:
        return

    scopes = find_for_scopes(text)
    if not scopes:
        return

    # Build a lookup: for each var, the list of (start, end) scopes
    seen: set[tuple[int, str, str]] = set()  # dedupe same var+chain on same line

    for var_match in VAR_RE.finditer(text):
        chain = var_match.group(1)
        root_var, attrs = analyze_chain(chain)
        if root_var in LOOP_LOCALS:
            continue

        # Is this chain inside a loop where root_var is the loop var?
        offset = var_match.start()
        active_scope = None
        for start, end, var in scopes:
            if start <= offset <= end and var == root_var:
                active_scope = (start, end, var)
                break
        if active_scope is None:
            continue

        line = line_number(text, offset)
        key = (line, root_var, chain)
        if key in seen:
            continue
        seen.add(key)

        # R2: terminal manager method
        if attrs and attrs[-1] in MANAGER_METHODS and len(attrs) >= 2:
            yield {
                'file': str(path),
                'line': line,
                'severity': 'medium',
                'issue': (
                    f"Template loop '{root_var}' accesses '{chain}' — "
                    f'reverse manager method inside loop, candidate for '
                    f"prefetch_related('{attrs[-2]}')"
                ),
            }
            continue

        # R1: FK traversal (>=2 attrs, last attr is not a safe primitive alone,
        # and the penultimate attr is not safe)
        if len(attrs) >= 2 and attrs[0] not in SAFE_ATTRS:
            yield {
                'file': str(path),
                'line': line,
                'severity': 'medium',
                'issue': (
                    f"Template loop '{root_var}' accesses '{chain}' — "
                    f'FK traversal inside loop, candidate for '
                    f"select_related('{attrs[0]}')"
                ),
            }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    parser.add_argument('--min-severity', choices=('low', 'medium', 'high'), default='low')
    args = parser.parse_args()

    threshold = SEVERITY_RANK[args.min_severity]
    root = args.path.resolve()

    print('Scanning Django templates for N+1 query candidates.', file=sys.stderr)

    findings = []
    for path in iter_template_files(root):
        findings.extend(
            finding
            for finding in scan_template(path)
            if SEVERITY_RANK[finding['severity']] >= threshold
        )

    if args.format == 'json':
        json.dump(findings, sys.stdout, indent=2)
        sys.stdout.write('\n')
        return 1 if findings else 0

    if not findings:
        print('No template N+1 candidates detected.')
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

    print(f'\nTotal: {len(findings)} candidates (hints, not confirmed bugs)')
    return 1


if __name__ == '__main__':
    sys.exit(main())

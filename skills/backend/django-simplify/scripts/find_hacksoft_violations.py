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
    ".venv",
    "venv",
    "env",
    ".env",
    "node_modules",
    ".git",
    "migrations",
    "__pycache__",
    "static",
    "media",
    "dist",
    "build",
    ".tox",
    "tests",
}

WRITE_VERBS = (
    "create",
    "update",
    "delete",
    "add",
    "remove",
    "assign",
    "issue",
    "cancel",
    "approve",
    "reject",
    "register",
    "bulk",
    "import",
    "sync",
    "publish",
    "archive",
)

NON_WRITE_PREFIXES = ("can_", "is_", "get_", "has_", "should_", "to_", "build_")

ORM_WRITE_CALLS = {
    "save",
    "create",
    "update",
    "delete",
    "bulk_create",
    "bulk_update",
    "get_or_create",
    "update_or_create",
}

VIEW_WRITE_METHODS = {
    "form_valid",
    "post",
    "put",
    "patch",
    "delete",
    "create",
    "update",
    "destroy",
    "perform_create",
    "perform_update",
    "perform_destroy",
}

FORM_WRITE_METHODS = {"save", "clean"}

ORM_WRITE_METHODS = {"save", "create", "bulk_create", "update", "delete", "bulk_update"}

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}


def iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def is_service_file(path: Path) -> bool:
    parts = path.parts
    if path.name == "services.py":
        return True
    return "services" in parts and path.suffix == ".py"


def is_view_file(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    return path.name in ("views.py", "apis.py", "viewsets.py") or any(
        p in parts for p in ("views", "apis", "viewsets")
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
    "authenticate",
    "get_user",
    "get_username",
    "get_by_natural_key",
    "has_perm",
    "has_module_perms",
    "get_all_permissions",
    "get_group_permissions",
    "configure_user",
    "clean_username",
}


def check_service_kwargs_only(func: ast.FunctionDef, path: Path):
    if func.name.startswith("_"):
        return
    if func.name in DJANGO_FRAMEWORK_OVERRIDES:
        return
    args = func.args
    has_positional = bool(args.args or args.posonlyargs)
    has_star_separator = args.vararg is not None or bool(args.kwonlyargs)
    if has_positional and not has_star_separator:
        yield {
            "file": str(path),
            "line": func.lineno,
            "severity": "medium",
            "issue": (
                f"Service '{func.name}' uses positional args (HackSoft: require `*,` keyword-only)"
            ),
        }


# ---------------------------------------------------------------------------
# Rule 2: write-like services must be @transaction.atomic
# ---------------------------------------------------------------------------


def _has_atomic_anywhere(func: ast.FunctionDef) -> bool:
    """Return True if the function is wrapped in transaction.atomic via decorator OR
    via a `with transaction.atomic():` / `with atomic():` block in the OUTER body only.

    Does NOT descend into nested FunctionDef / AsyncFunctionDef / Lambda — atomic
    wrapping inside an inner function does not protect the outer service.
    """
    # Decorator-level check.
    if has_decorator(func, "transaction.atomic") or has_decorator(func, "atomic"):
        return True

    # Iterative BFS/DFS that stops at nested function boundaries.
    nested_func_types = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
    queue = list(ast.iter_child_nodes(func))
    while queue:
        node = queue.pop()
        if isinstance(node, nested_func_types):
            # Do not recurse into nested functions.
            continue
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                try:
                    src = ast.unparse(item.context_expr)
                except (AttributeError, ValueError):
                    continue
                if "atomic" in src:
                    return True
        queue.extend(ast.iter_child_nodes(node))
    return False


def _has_atomic_block_assert(func: ast.FunctionDef) -> bool:
    """Return True if the function contains `assert connection.in_atomic_block`,
    which signals that the caller is responsible for providing the transaction.

    Only scans the outer function body — does not descend into nested functions.
    """
    nested_func_types = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
    queue = list(ast.iter_child_nodes(func))
    while queue:
        node = queue.pop()
        if isinstance(node, nested_func_types):
            continue
        if isinstance(node, ast.Assert):
            try:
                src = ast.unparse(node.test)
            except (AttributeError, ValueError):
                pass
            else:
                if "in_atomic_block" in src:
                    return True
        queue.extend(ast.iter_child_nodes(node))
    return False


def _is_inside_loop(ancestors: list[ast.AST]) -> bool:
    """Return True if any ancestor in the list is a For / AsyncFor / While node."""
    return any(isinstance(a, (ast.For, ast.AsyncFor, ast.While)) for a in ancestors)


def _count_orm_writes(func: ast.FunctionDef) -> int:
    """Count distinct ORM write call-sites in the function body.

    Only counts primary write verbs from ORM_WRITE_CALLS (save, create, update,
    delete, bulk_create, bulk_update, get_or_create, update_or_create).  M2M
    helpers like add/remove/set are intentionally excluded because they are
    frequently used as secondary side-effects and counting them would
    over-flag utility functions like model_update.

    Special case: `update()` called on a plain variable (ast.Name receiver) is
    likely a dict/list mutation, not an ORM QuerySet update — it is excluded.
    ORM update is always chained (queryset.filter(...).update(...)), so its
    receiver is an ast.Call or ast.Attribute, not a bare ast.Name.

    Loop-write rule: a single ORM write inside a for/while loop executes once
    per iteration, breaking atomicity across iterations exactly like two separate
    writes.  If any write is found inside a loop body the function is treated as
    having ≥2 writes regardless of the raw call-site count.
    """
    nested_func_types = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)

    count = 0
    has_loop_write = False

    # Walk the outer function body only, tracking ancestor nodes.
    # We use an explicit stack of (node, ancestors) pairs.
    stack: list[tuple[ast.AST, list[ast.AST]]] = [
        (child, []) for child in ast.iter_child_nodes(func)
    ]
    while stack:
        node, ancestors = stack.pop()

        # Stop at nested function boundaries — their writes are not ours.
        if isinstance(node, nested_func_types):
            continue

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr in ORM_WRITE_CALLS and not (
                attr == "update" and isinstance(node.func.value, ast.Name)
            ):
                # Exclude dict.update() / set-like .update() on plain local variables.
                count += 1
                if _is_inside_loop(ancestors):
                    has_loop_write = True

        child_ancestors = ancestors + [node]
        stack.extend((child, child_ancestors) for child in ast.iter_child_nodes(node))

    # A single write inside a loop is equivalent to ≥2 writes: report at least 2
    # so the ≥2 threshold in the caller fires correctly.
    if has_loop_write and count < 2:
        return 2
    return count


def check_service_transaction_atomic(func: ast.FunctionDef, path: Path):
    if func.name.startswith("_") or not looks_like_write(func.name):
        return
    if any(func.name.lower().startswith(p) for p in NON_WRITE_PREFIXES):
        return
    if not _has_orm_write_in_body(func):
        return
    # Fix #2: scan the WHOLE body for atomic wrapping (not just first statement).
    if _has_atomic_anywhere(func):
        return
    # Fix #2: `assert connection.in_atomic_block` means caller owns the transaction.
    if _has_atomic_block_assert(func):
        return
    # Fix #3: single-write services are already atomic — only flag ≥2 writes.
    if _count_orm_writes(func) < 2:
        return
    yield {
        "file": str(path),
        "line": func.lineno,
        "severity": "high",
        "issue": (
            f"Service '{func.name}' looks like a write but is not wrapped in @transaction.atomic"
        ),
    }


# ---------------------------------------------------------------------------
# Rule 3: save() without preceding full_clean()
# ---------------------------------------------------------------------------


def check_save_without_full_clean(tree: ast.AST, path: Path):
    for parent in ast.walk(tree):
        body = getattr(parent, "body", None)
        if not isinstance(body, list):
            continue
        for i, stmt in enumerate(body):
            call = _extract_save_call(stmt)
            if call is None:
                continue
            func = call.func
            if not isinstance(func, ast.Attribute):
                continue
            target = func.value
            if not isinstance(target, ast.Name):
                continue
            if target.id in ("self", "super", "cls"):
                continue
            if _cleaned_before(body, i, target.id):
                continue
            yield {
                "file": str(path),
                "line": stmt.lineno,
                "severity": "low",
                "issue": (
                    f"'{target.id}.save()' called without prior "
                    f"'{target.id}.full_clean()' "
                    "(advisory — review if this is a Django model)"
                ),
            }


def _extract_save_call(stmt: ast.stmt) -> ast.Call | None:
    if not isinstance(stmt, (ast.Expr, ast.Assign)) or not isinstance(
        stmt.value, ast.Call
    ):
        return None
    call = stmt.value
    if isinstance(call.func, ast.Attribute) and call.func.attr == "save":
        return call
    return None


def _cleaned_before(body: list, index: int, var_name: str) -> bool:
    needle = f"{var_name}.full_clean"
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
    end = getattr(func, "end_lineno", func.lineno)
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
            if isinstance(base, ast.Name) and base.id not in ("self", "super", "cls"):
                score += 3
    if score >= 6:
        yield {
            "file": str(path),
            "line": func.lineno,
            "severity": "medium",
            "issue": f"View method '{func.name}' contains business logic — delegate to services.py",
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
    is_form = class_inherits(cls, "Form")
    is_serializer = class_inherits(cls, "Serializer")
    if not (is_form or is_serializer):
        return
    kind = "Form" if is_form else "Serializer"
    target_methods = FORM_WRITE_METHODS if is_form else {"create", "update", "save"}
    for node in cls.body:
        if not isinstance(node, ast.FunctionDef) or node.name not in target_methods:
            continue
        for sub in ast.walk(node):
            if not (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)):
                continue
            if sub.func.attr in ORM_WRITE_METHODS:
                base = sub.func.value
                if isinstance(base, ast.Name) and base.id in ("self", "super", "cls"):
                    continue
                yield {
                    "file": str(path),
                    "line": sub.lineno,
                    "severity": "medium",
                    "issue": (
                        f"{kind} '{cls.name}.{node.name}()' performs ORM write "
                        "— move to services.py"
                    ),
                }
                break


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def scan_file(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
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
    parser.add_argument("path", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--min-severity", choices=("low", "medium", "high"), default="low"
    )
    args = parser.parse_args()

    threshold = SEVERITY_RANK[args.min_severity]
    root = args.path.resolve()

    findings = []
    for path in iter_python_files(root):
        findings.extend(
            finding
            for finding in scan_file(path)
            if SEVERITY_RANK[finding["severity"]] >= threshold
        )

    if args.format == "json":
        json.dump(findings, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1 if findings else 0

    if not findings:
        print("No HackSoft styleguide violations detected.")
        return 0

    grouped: dict[str, list[dict]] = {"high": [], "medium": [], "low": []}
    for f in findings:
        grouped[f["severity"]].append(f)

    for sev in ("high", "medium", "low"):
        items = grouped[sev]
        if not items:
            continue
        print(f"\n=== {sev.upper()} ({len(items)}) ===")
        for f in items:
            print(f"  {f['file']}:{f['line']}")
            print(f"      {f['issue']}")

    print(f"\nTotal: {len(findings)} violations")
    return 1


if __name__ == "__main__":
    sys.exit(main())

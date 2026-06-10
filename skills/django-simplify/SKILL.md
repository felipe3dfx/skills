---
name: django-simplify
description: Audit Django codebases for Django-specific structural problems — N+1 queries, missing select_related/prefetch_related, fat views/models, ORM anti-patterns, unbounded querysets, hardcoded URLs, abstract models with one child, unnecessary signals, and premature service layers. Use when the user asks to audit, simplify, refactor, or find anti-patterns in Django code. Complements the generic `simplify` skill (which handles any changed code) — this one focuses on whole-project Django analysis.
---

# Django Simplify

Structural audit of Django projects. Detects Django-specific anti-patterns and over-engineering that generic linters (ruff, ty) do NOT catch.

## When to use

- "Audit this Django project / find tech debt"
- "Find N+1 queries"
- "Detect Django anti-patterns"
- "Optimize QuerySets / ORM calls"
- "Find fat views or fat models"
- "Check for over-engineered abstractions"
- User explicitly asks for a Django structural audit

## When NOT to use

- **Generic code review of recently-changed code** → use `simplify` (Anthropic plugin)
- **Style, formatting, unused imports, type errors** → `ruff check`, `ty check`
- **Security scanning** → `bandit`
- **How to FIX issues** → `django-expert` (teaches patterns); this skill only DETECTS them
- **Non-Django Python projects** → this skill assumes Django imports and ORM usage
- **Automatic background cleanup after edits**
- **Broad whole-project scans without explicit user request**

## Activation Guard

This skill is intentionally expensive compared to incremental review.

- Do **not** run automatically after features, bugfixes, or routine edits.
- Do **not** start with a whole-project audit unless the user explicitly asks for it.
- Prefer a bounded scope first: one app, one package, one problem class, or one script category.
- If the request is ambiguous, stop and ask whether the user wants:
  - a narrow targeted audit, or
  - a full-project audit

Default to the narrower option.

## Scripts

All scripts live in `scripts/` and are standalone — they scan a project directory and output `file:line` with severity.

| Script | Detects |
|--------|---------|
| `find_django_issues.py` | N+1 risks (`.all()` in loops), missing `select_related` / `prefetch_related`, hardcoded URLs, fat views (100+ lines) |
| `find_django_antipatterns.py` | `save`/`create`/`delete` in loops, unbounded querysets, raw SQL, `update()` without `F()`, fat models, `mark_safe` misuse, hardcoded secrets, `DEBUG=True`, missing `__str__` |
| `find_django_overengineering.py` | Abstract models with one child, unused abstract models, single-method managers, signals for trivial logic, single-use mixins, deep form inheritance, service layers wrapping plain CRUD |
| `find_multitenant_leaks.py` | Queries in views/APIs/selectors that skip the tenant filter (customer, organization, workspace…). Reads the tenant field from `pyproject.toml` under `[tool.django-simplify.tenant] field = "..."`, or auto-detects from model FKs. Silently skips in non-multi-tenant projects. |
| `find_hacksoft_violations.py` | Services without keyword-only args (`*,`), write-like services without `@transaction.atomic`, `save()` without preceding `full_clean()`, business logic in views / forms / serializers. |
| `find_model_safety.py` | Any FK with `on_delete=CASCADE` (review case by case), `null=True` on `CharField`/`TextField`, missing `max_length`, `DecimalField` missing `max_digits`/`decimal_places`, models without `Meta.ordering`. |
| `find_template_nplus1.py` | N+1 query candidates in Django templates — loops accessing chained FK attributes (`{{ obj.customer.name }}`) → `select_related` candidates; loops calling reverse manager methods (`{{ obj.items.count }}`) → `prefetch_related` candidates. Regex-based, hints only (cannot see the view). |

## Usage

```bash
python scripts/find_django_issues.py /path/to/project
python scripts/find_django_antipatterns.py /path/to/project
python scripts/find_django_overengineering.py /path/to/project
python scripts/find_multitenant_leaks.py /path/to/project
python scripts/find_hacksoft_violations.py /path/to/project
python scripts/find_model_safety.py /path/to/project
python scripts/find_template_nplus1.py /path/to/project

# Multi-tenant: override the tenant field (useful in CI or one-off runs)
python scripts/find_multitenant_leaks.py . --tenant-field organization

# HackSoft: only high-severity violations
python scripts/find_hacksoft_violations.py . --min-severity high

# Filter by category or severity
python scripts/find_django_antipatterns.py . --category performance
python scripts/find_django_antipatterns.py . --category security
python scripts/find_django_antipatterns.py . --min-severity medium

# JSON output for CI / tooling
python scripts/find_django_issues.py . --format json > report.json
```

## Workflow

1. **Choose the narrowest useful scope first**
2. **Run only the relevant script(s)** for the user's question
3. Expand to additional scripts only when findings justify it or the user requests a broader audit
4. **Prioritize**: high → medium → low (security > performance > maintainability)
5. **For each issue**: navigate to `file:line`, understand the context
6. **Apply the fix**: consult `references/django-patterns.md` or invoke the `django-expert` skill for detailed guidance
7. **Re-run only the relevant script** to confirm the issue is resolved
8. **One fix at a time** — don't batch unrelated refactors

Avoid the old habit of "run everything first" unless the user explicitly wants a full audit.

## Resource Guard

When auditing:
- Start with the smallest path scope possible
- Start with the most relevant detector instead of all detectors
- Avoid repeated full scans after every small fix
- Re-run only the detector(s) affected by the fix
- If a scan could be heavy on a large codebase, warn the user before expanding scope

Recommended progression:
1. single app or package
2. single detector category
3. broaden only if needed

Rule of thumb:
- signal first
- coverage second
- exhaustiveness last

## Principles

1. **YAGNI** — abstract models, managers, signals should have a concrete reason to exist
2. **Detection ≠ fix** — this skill finds problems; `django-expert` teaches solutions
3. **Measure before optimizing** — N+1 detection finds *candidates*, not always problems (depends on loop size)
4. **Preserve behavior** — refactors must not change functionality; add tests first if missing
5. **Django built-ins > custom code** — prefer `bulk_create`, `F()`, `update()`, `select_related` over manual loops
6. **Explicit Activation** — whole-project audits must be user-requested, not implied
7. **Machine-Aware Scoping** — prefer targeted scans over exhaustive scans by default

## Related skills

- **`simplify`** (Anthropic plugin) — Use for incremental review of recently-changed code, any language. Complementary: `simplify` reviews diffs, `django-simplify` audits whole projects.
- **`django-expert`** — Use AFTER this skill finds issues, to learn *how* to fix them (patterns, best practices, architecture guidance). `django-simplify` detects; `django-expert` teaches.

## References

See `references/django-patterns.md` for:
- N+1 prevention (`select_related` vs `prefetch_related`)
- Bulk operations (`bulk_create`, `update()`, `F()` expressions)
- Fat view → thin view refactoring
- Signal alternatives (explicit methods)
- URL best practices (`reverse()`, named URLs)
- Model best practices (`__str__`, `TextChoices`, `related_name`, indexes)
- Security checklist (`mark_safe`, secrets, ownership checks)

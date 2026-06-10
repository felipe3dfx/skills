---
name: simplify
description: Simplifies and refines recently-modified Python code for clarity, consistency, and maintainability while preserving all functionality. Use for incremental code review after changes, NOT for whole-project audits.
trigger:
  - "Simplify this code"
  - "Make this clearer"
  - "Review the code I just wrote"
---

# Simplify

Refines recently-modified code for clarity and maintainability. Preserves exact functionality—only improves how the code expresses it.

## When to Use

- User asks "make this cleaner" or "review my changes"
- User explicitly requests simplification/refinement of code
- You have a narrow, explicit target scope

## When NOT to Use

- **Whole-project Django audit** → `django-simplify` (detects N+1, fat views, ORM issues)
- **Style/formatting fixes** → `ruff check --fix`
- **Learning Django patterns** → `django-expert`
- **Security review** → `bandit`
- **Automatic post-edit cleanup without user request**
- **Large diffs, broad refactors, or ambiguous scope**

## Scope

Only code modified in the **current session** or **recent commits** (default: last 10 files changed). Do NOT review unchanged code unless explicitly asked.

Hard guards:
- Do **not** run automatically after every feature/bugfix/edit.
- Prefer explicit file paths or a tightly-bounded diff.
- If scope is broad or ambiguous, stop and ask the user to narrow it.
- Never turn this into a repo-wide pass unless the user explicitly requests that.

## Principles

1. **Preserve Behavior** — Never change what code does, only how it does it
2. **Clarity > Brevity** — Explicit code beats dense one-liners
3. **Balance** — Don't over-abstract; don't remove useful abstractions
4. **Project Standards** — Follow CLAUDE.md conventions
5. **Explicit Activation** — Run `simplify` only when the user asks for it or provides a clearly bounded target
6. **Machine-Aware Verification** — Never assume aggressive parallel test execution is safe

## Refinement Checklist

### Naming
- [ ] Variables: nouns describing the data (`user_count`, not `uc`)
- [ ] Functions: verbs describing the action (`get_active_users`, not `users`)
- [ ] Booleans: `is_`, `has_`, `should_` prefixes (`is_valid`, not `valid`)
- [ ] Constants: `UPPER_SNAKE_CASE` at module level
- [ ] Django models: singular (`Order`, not `Orders`)
- [ ] Avoid abbreviations unless domain-standard (`id`, `url` ok; `usr`, `obj` no)

### Structure
- [ ] Functions do ONE thing (Single Responsibility)
- [ ] Early returns instead of nested if/else pyramids
- [ ] Guard clauses at function start
- [ ] No nested ternaries — use if/elif/else or match/case
- [ ] Extract complex conditionals to named booleans
- [ ] List/dict comprehensions only when readable (not nested)

### Django/HTMX Specifics
- [ ] View functions: thin, delegate to services/selectors
- [ ] URL construction: use `reverse()` or `get_absolute_url()`, never hardcoded
- [ ] HTMX triggers: explicit `hx-target`, `hx-swap` values
- [ ] Form handling: validate early, fail fast
- [ ] Template context: minimal, explicit variable names

### Python Idioms
- [ ] Prefer `is`/`is not` for None checks
- [ ] Use `if value:` for truthiness, not `if value is not None:` (unless None is valid value)
- [ ] F-strings for formatting (not `%` or `.format()`)
- [ ] Context managers (`with`) for resources
- [ ] Walrus operator `:=` only when it improves clarity
- [ ] Type hints on public functions (not internal helpers unless complex)

### Docstrings & Comments
- [ ] Remove comments stating the obvious
- [ ] Add comments explaining WHY, not WHAT
- [ ] Docstrings for public APIs: args, returns, raises
- [ ] No commented-out code — delete it (git has history)

## Process

1. **Identify modified code** — Check `git diff` or recent session edits
2. **Analyze each changed function/class** against checklist
3. **Apply refinements** — Edit in place, preserve behavior
4. **Verify (only when requested)** — Run tests/checks only if the user explicitly asks for verification
5. **Summarize** — Brief bullet list of improvements made

## Verification Guard

Do **not** run tests automatically as part of `simplify`.

Only run tests when one of these is true:
- The user explicitly asks to run tests
- The invoking workflow explicitly requires verification

When tests are requested:
- Prefer the smallest relevant test scope first
- Avoid `pytest -n auto` or any machine-saturating default
- Respect the machine's capacity; choose conservative parallelism
- If the repo uses `xdist`, prefer one of these approaches unless the user asks otherwise:
  - run serially (`-n 0` or no `-n`)
  - or use a small fixed worker count appropriate to the machine
- If you cannot determine a safe parallel setting, default to serial execution

Rule of thumb:
- correctness first
- resource safety second
- speed third

If the likely test command will spawn many workers/processes, warn the user and propose a safer command before executing it.

## Example Transformations

### Before
```python
def get_data(r, t):
    if t == 'active':
        s = User.objects.filter(is_active=True)
    elif t == 'staff':
        s = User.objects.filter(is_staff=True)
    else:
        s = User.objects.all()
    return s[:r]
```

### After
```python
def get_users(limit: int, filter_type: str) -> QuerySet[User]:
    """Return users filtered by type, limited to N results."""
    queryset = User.objects.all()

    if filter_type == 'active':
        queryset = queryset.filter(is_active=True)
    elif filter_type == 'staff':
        queryset = queryset.filter(is_staff=True)

    return queryset[:limit]
```

### Before
```python
if user and user.is_authenticated and user.is_staff and not user.is_banned:
    show_admin_panel = True
else:
    show_admin_panel = False
```

### After
```python
is_authorized_admin = (
    user
    and user.is_authenticated
    and user.is_staff
    and not user.is_banned
)
show_admin_panel = is_authorized_admin
```

## Related Skills

- **`django-simplify`** — Whole-project Django audit (N+1, fat views, ORM patterns). Use for periodic audits, NOT incremental review.
- **`django-expert`** — Learn HOW to implement Django patterns. Use when you need guidance on approach, not refinement.
- **`pytest`** — Write tests before/after refactoring. Use to ensure behavior preservation.

## Output

After simplifying, provide:
- Summary of what was improved (2-3 bullets)
- Any trade-offs or follow-up actions
- Whether verification was run or intentionally skipped
- If verification ran, the result and the execution mode used (e.g. serial or limited parallelism)

---
name: simplify
description: "Trigger: simplify, clean up, or review recent code changes. Refines code safely; uses deep multi-review only for risk signals."
metadata:
  version: 1.1.0
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
- User asks for deep simplification, or the scoped diff has structural risk signals
- An orchestrating skill (e.g. `review`) delegates a bounded PR diff — see
  [Delegated Mode](#delegated-mode-invoked-by-review)

## When NOT to Use

- **Whole-project Django audit** → `django-simplify` (detects N+1, fat views, ORM issues)
- **Style/formatting fixes** → `ruff check --fix`
- **Learning Django patterns** → `django-expert`
- **Security review** → `bandit`
- **Automatic post-edit cleanup without user request** (does not apply when
  `review` delegates — see Delegated Mode)
- **Unbounded broad refactors or ambiguous scope** (does not apply when
  `review` delegates a defined PR diff — see Delegated Mode). Large but bounded
  diffs may use deep simplify when [risk signals](#mode-selection) justify it.

## Mode Selection

Use **normal simplify** by default. Use **deep simplify** only when risk signals
justify the extra sub-agent cost. Size is a signal, not the rule.

| Signal | Mode |
| --- | --- |
| User explicitly asks for `deep simplify`, `parallel simplify`, or a focus like `reuse`, `quality`, `efficiency` | Deep simplify |
| Diff is large, e.g. >400 changed lines or >=4 non-trivial code files | Deep simplify |
| Diff touches boundaries: auth, permissions, routing, storage, caching, migrations, startup, task queues, public APIs | Deep simplify |
| Diff adds helpers/utilities, registries, abstractions, cross-file wiring, or likely duplicate logic | Deep simplify |
| Diff touches hot paths: DB queries, loops over unbounded data, repeated IO/API calls, per-request/startup work | Deep simplify |
| Docs, generated files, formatting-only changes, mechanical renames, repetitive fixtures/tests | Normal simplify or skip |

Deep simplify is **not** automatic just because a diff is long. If a long diff is
mechanical or generated, do not fan out. If a short diff crosses an important
boundary, use deep simplify.

## Delegated Mode (invoked by `review`)

When an orchestrating skill such as `review` invokes this skill on a PR, the
default standalone contract is overridden as follows. The delegation itself
**is** the explicit activation — do not balk or ask the user to narrow scope.

- **Scope = the PR diff.** The changed files in the PR are the bounded target,
  even when the diff is large or spans many files. The large-diff guard does
  not apply: `review` is responsible for prioritization, you cover what it routes.
- **Report, do not edit.** Do **not** edit in place. Produce *findings* for
  `review` to fold into its report — never modify files. A review is read-only
  and validates with the user before posting; an editing sub-step would break
  that contract.
- **Finding format** — each finding is a three-part unit, written in **Spanish**
  to match `review`'s output language:
  - **Qué** — the specific simplification opportunity
  - **Por qué** — the technical reason it improves the code
  - **Cómo** — a concrete direction, with a before/after sketch when it helps
- **Non-blocking by default.** Simplifications are suggestions, not merge
  blockers, unless the impact is significant. Surface them either way.
- **No tests.** Verification belongs to `review`'s automated-checks step; do
  not run tests from the delegated path.

Everything below this section describes the default standalone behavior used
when a human invokes `simplify` directly.

## Deep Simplify Mode

Deep simplify runs focused reviewers in parallel, then the primary agent
deduplicates findings and applies only safe refinements.

Core principle: three narrow reviewers beat one broad reviewer when the diff has
real review risk. Each reviewer searches deeply for one class of problem —
reuse, quality, or efficiency — without diluting attention across all three.

Recognized user modifiers:
- **Focus**: `reuse`, `quality`, or `efficiency` runs only that reviewer or
  weights aggregation toward it.
- **Dry run**: `dry-run`, `just report`, or `don't change anything` reports
  findings and applies nothing.
- **Scope**: `staged`, `last commit`, `branch`, or explicit file paths narrow
  the diff source.

Reviewer prompts:
- **Reuse reviewer** — search the existing codebase for helpers, constants,
  registries, or patterns the diff duplicates. Require `file:line` evidence.
- **Quality reviewer** — find redundant state, parameter sprawl,
  copy-paste-with-variation, leaky abstractions, and stringly-typed code where
  a canonical enum/constant/registry already exists.
- **Efficiency reviewer** — find repeated work, N+1 access, missed concurrency,
  hot-path bloat, TOCTOU patterns, unbounded memory growth, and overly broad
  reads.

Each reviewer must return: `file:line → problem → suggested fix → confidence`
and skip style-only nits. Drop findings without concrete evidence.

Reviewer launch rules:
- Do not fan out wider than the three reviewer categories. More reviewers add
  cost and conflict, not better coverage.
- Give every reviewer the whole relevant diff, not fragments. Cross-file
  duplication, N+1s, and abstraction leaks hide in partial diffs.
- Include the absolute repository path and instruct reviewers to search the
  wider codebase for evidence. Reviewers must not reason from the diff alone.
- Fold project conventions into the reviewer prompt when present: `AGENTS.md`,
  `CLAUDE.md`, `HERMES.md`, formatter/linter config, or local style docs.
- If the diff is huge, e.g. >2000 changed lines, warn that three reviewers will
  be token-heavy and ask to scope by directory, commit, or file unless the user
  explicitly accepts the cost.

Aggregation rules:
1. Merge and dedupe overlapping findings.
2. Discard weak or speculative suggestions silently.
3. Resolve conflicts by: **correctness > user focus > readability/reuse > micro-performance**.
4. Never apply a performance suggestion that hurts clarity unless the path is
   genuinely hot and the evidence supports it.
5. When two suggestions are mutually exclusive and both defensible, prefer the
   one that touches less code and note the alternative.
6. Apply only scoped behavior-preserving fixes unless dry-run was requested.
   Apply does not mean rewrite: touch the diff and minimal surrounding code only.
7. Mention skipped findings only when the trade-off matters.

## Scope

Only code modified in the **current session** or **recent commits** (default: last 10 files changed). Do NOT review unchanged code unless explicitly asked.

Choose the diff source in this order unless the user specifies otherwise:
1. `git diff` for unstaged tracked changes
2. `git diff HEAD` when the working-tree diff is empty but staged changes exist
3. `git diff --staged`, `git diff HEAD~1`, `git diff main...HEAD`, or
   `git diff -- <path>` for explicit user scopes
4. Recently edited/named files from the session if there is no useful git diff

If there is no git diff, no explicit file scope, and no recent edited files,
stop and say there is nothing to simplify.

Hard guards:
- Do **not** run automatically after every feature/bugfix/edit. (Delegation by
  `review` is an explicit invocation, not automatic post-edit cleanup.)
- Prefer explicit file paths or a tightly-bounded diff.
- If scope is broad or ambiguous, stop and ask the user to narrow it. (In
  Delegated Mode the PR diff is the bound — do not ask.)
- Never turn this into a repo-wide pass unless the user explicitly requests that.

## Principles

1. **Preserve Behavior** — Never change what code does, only how it does it
2. **Clarity > Brevity** — Explicit code beats dense one-liners
3. **Balance** — Don't over-abstract; don't remove useful abstractions
4. **Project Standards** — Follow CLAUDE.md conventions
5. **Explicit Activation** — Run `simplify` only when the user asks for it, provides a clearly bounded target, or an orchestrating skill (`review`) delegates a PR diff
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
2. **Select mode** — Use [Mode Selection](#mode-selection); do not equate size with risk
3. **Normal path** — Analyze each changed function/class against the checklist
4. **Deep path** — Launch the relevant focused reviewers in parallel when available; if sub-agent delegation is unavailable, state that and fall back to normal simplify unless the user requested deep-only
5. **Apply refinements** — Edit in place, preserve behavior (in [Delegated Mode](#delegated-mode-invoked-by-review): report findings instead of editing)
6. **Verify (only when requested)** — Run tests/checks only if the user explicitly asks for verification
7. **Summarize** — Brief bullet list of improvements made

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
- **`review`** — PR review orchestrator that delegates simplification of changed files to this skill. When invoked from `review`, follow [Delegated Mode](#delegated-mode-invoked-by-review).

## Output

After simplifying, provide:
- Summary of what was improved (2-3 bullets)
- Mode used: normal simplify or deep simplify, with the trigger signal
- Any trade-offs or follow-up actions
- For deep simplify: findings applied, findings skipped, and reviewer categories used
- Whether verification was run or intentionally skipped
- If verification ran, the result and the execution mode used (e.g. serial or limited parallelism)

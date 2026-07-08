---
name: review
description: "Review PRs or branch diffs: verify Spec fit, Standards/design quality, delegated domain rules, CI evidence, and safe posting."
metadata:
  author: grupo-ilao
  version: "2.0"
---

## Purpose

Review pull requests or branch diffs as an orchestrator, not a rules container. Keep three axes independent:

1. **Spec / problem fit** — does the change solve the stated problem, without missing requirements or scope creep?
2. **Standards / design quality** — does it follow documented standards, delegated domain rules, and design heuristics?
3. **CI evidence** — do GitHub checks for the PR head pass when a PR exists?

One axis must not hide another: clean code can solve the wrong problem, and correct behavior can still violate project standards.

Delegate domain rules to available project skills (`django-expert`, `django-pytest`, `htmx`, `huey`, `django-simplify`, `simplify`, `tailwind-4`, `alpinejs`, `django-components`) and project docs (`AGENTS.md`, `docs/agents/AGENTS.md`, `docs/`). One source of truth per domain. If a relevant skill is unavailable, use repository docs and current code evidence.

Apply these cross-cutting lenses inline inside the relevant domain review. Do not treat this skill as permission to spawn subagents. Extra reviewers may be launched only by the active orchestrator/harness according to its delegation policy, or by explicit user request.

| Lens | Use when the change touches | Look for |
| --- | --- | --- |
| Risk | auth, permissions, user input, settings, public APIs, dependencies | authorization, secrets, raw HTML/SQL/commands, cookie/security flags, dependency evidence |
| Readability | large/unclear diffs, duplicated code, complex functions, vague PR context | intent-revealing names, dead code, magic values, duplicated logic, reviewable scope |
| Reliability | tests, behavior changes, importers, contracts, edge cases | behavior-first tests, invalid/empty/failure paths, deterministic outputs, useful coverage |
| Resilience | async tasks, external services, retries, performance, operations | fallback/retry behavior, observability, rollback/fix-forward path, user-visible performance risk |

## Step 1 — Gather Context

**Choose the branch**:

- **PR review**: fetch title, description, author, base branch, changed files, diff stats, inline comments, unresolved threads, review history, and CI context.
- **Branch/WIP diff review**: require a fixed point (`main`, branch, tag, commit SHA, `HEAD~N`). Validate it with `git rev-parse <fixed-point>`, compare with `git diff <fixed-point>...HEAD`, and confirm the diff is non-empty. Mark platform-only steps (review history, CI, posting) as not applicable unless a PR exists.

**Identify the problem/spec source** in this order:

1. Linked Linear issue from PR title (`ILA-\d+`), branch name, or commit messages.
2. PR description or user-provided issue/spec/PRD path.
3. A matching file under `docs/`, `specs/`, or project planning docs.
4. If no source is found, ask the user for the problem context before reviewing.

**Read standards sources**: root `AGENTS.md`, then `docs/agents/AGENTS.md` when present. Follow the project guides they route to for structure, style, patterns, and testing concerns. Also determine the target Python version from project evidence (`pyproject.toml`, `.python-version`, Docker/CI config) before making syntax-compatibility claims.

**Check previous review rounds for PR reviews**: read prior comments and verify each claimed fix in the current code. A DISMISSED review may have been auto-dismissed by a new commit; compare the review `commit_id` to current HEAD. When prior reviews reference inline comments, verify they were submitted through the GitHub API.

**Done when** the review branch is known, target diff is non-empty, changed files are known, problem context is available or explicitly missing, standards sources are identified, and PR-only obligations are checked or marked not applicable.

## Step 2 — Spec / Problem Fit Pass

Review this axis independently from style or design quality. Well-written code can still fail to fix the problem.

- **Trace the full flow**: follow data from entry point, through every touched layer, to where it exits or is consumed.
- **Find the exit condition**: if something retries or queues repeatedly, verify how it leaves the retry/processing loop.
- **Check the abstraction level**: a fix below or above the root-cause layer is a workaround until proven otherwise.
- **Compare behavior**: when a property, method, or function is replaced, state the behavior changed from X to Y.
- **Check coverage against the spec**: quote or reference the requirement for each missing, partial, wrong, or scope-creep finding. If no spec exists, state that the Spec pass is limited to PR/user-provided context.

**Done when** every acceptance criterion or problem statement has a verdict: satisfied, missing, partial, out of scope, or unreviewable due to missing context.

## Step 3 — PR Size Heuristic

Before deep file review, measure additions and files changed.

- If additions > 500 lines OR files changed > 20, use that as an internal risk signal and prioritize critical correctness/design findings.
- Mention size only when it materially prevents a reliable review or hides actionable risk.

**Done when** review-depth risk is known and the review scope has been prioritized accordingly.

## Step 4 — Apply Project Standards via Delegation

Load and apply relevant project skills by touched file type. Each skill is canonical for its domain; keep domain rules in that skill or local references. If a listed skill is unavailable, continue with `AGENTS.md`, `docs/`, and current code evidence.

| Path pattern | Skills / reference |
| --- | --- |
| `apps/**/services*.py`, `apps/**/services/*.py` | `django-expert`, `django-simplify`, `simplify` |
| `apps/**/managers.py`, `apps/**/managers/*.py` | `django-expert`, `django-simplify` |
| `apps/**/views*.py`, `apps/**/forms*.py`, `apps/**/models*.py` | `django-expert`, `django-simplify`, `simplify` |
| `apps/**/*_tests.py`, `apps/**/tests/**/*.py` | `django-pytest`, plus `references/test-review-quality.md` |
| `apps/**/tasks.py`, `apps/**/tasks/*.py` | `huey`, Resilience lens |
| `apps/**/api.py`, `apps/**/api/*.py` | `django-expert`, API docs/current code, Risk lens |
| `apps/**/migrations/*.py` | `references/migration-review-rules.md` |
| `**/*.html` with `hx-*` attributes | `htmx` |
| `**/*.html` with `x-data` / `x-bind` / `x-show` / `x-on` | `alpinejs` |
| `**/*.html`, `**/*.css` with Tailwind classes | `tailwind-4` |
| `components/**/*` | `django-components` |
| `tests/e2e/**/*.py`, `tests/e2e/**/*.ts` | available e2e/browser-testing guidance or manual review |

For any Python change, also apply project-wide coding standards routed from `docs/agents/AGENTS.md` or the equivalent project documentation router.

**Done when** every changed file is routed to a domain skill, local reference, project standard, or explicit manual rule; missing skill coverage is called out as a limitation.

## Step 5 — Standards / Design Pass

Apply these cross-cutting heuristics after domain rules. Documented project rules win over generic smells. Treat smells as judgment calls, not automatic blockers.

- **Model relationships**: when relationships change, apply `django-expert` and `django-simplify` source-of-truth rules.
- **Encapsulation**: importing private symbols (`_name`) from another module signals misplaced responsibility; make the symbol public or move it to a shared module.
- **Mysterious names**: names should reveal intent; if no honest name exists, the design is likely unclear.
- **Duplicated code**: repeated logic shape should be extracted or centralized unless project standards intentionally prefer duplication there.
- **Feature envy / message chains**: logic reaching deeply into another object's data belongs closer to that data or behind a clearer method.
- **Single Responsibility**: split units that have independently evolving reasons to change.
- **Implicit contracts**: parsing exception message strings creates silent cross-module contracts; use typed exceptions or explicit result objects.
- **Transactions**: services performing multiple writes, or catching `IntegrityError`, need `transaction.atomic`.
- **Bulk writes**: one write per object in a loop should usually become `bulk_create` / `bulk_update`.
- **Data clumps / missing abstraction**: values traveling together across signatures should become a structure.
- **Primitive obsession**: meaningful domain concepts deserve explicit types/objects instead of repeated strings, numbers, or booleans.
- **Speculative generality**: remove abstractions, parameters, hooks, or extension points not required by the current spec.
- **Unreachable or redundant control flow**: investigate; it often signals misunderstood execution.
- **Python-version-sensitive syntax**: verify the target Python version before flagging syntax. In Python 3.14+, `except A, B:` is valid for multiple exception types when there is no `as` binding; parentheses are still required for `except (A, B) as exc:`.
- **Behavior-preserving simplifications**: surface unnecessary defensive code, avoidable cost, redundant variables, or clearer expression opportunities when impact is meaningful.

For project-specific blocking criteria, follow the target repository's `docs/agents/AGENTS.md` and review-routing docs. Do not keep project policy inside this installed skill.

**Done when** each Standards/design finding is tied to a documented rule, delegated skill, local reference, or named heuristic, with severity justified by current code evidence.

## Step 6 — Inspect GitHub CI Checks

For PR reviews, validate automated checks from the PR's GitHub check runs / CI status. For branch/WIP diff reviews without a PR, mark CI as not applicable instead of running local project tooling.

Fetch current GitHub checks for the PR head commit:

- If a check failed, quote the failing check name and summarize GitHub's output/log snippet when available.
- If checks are pending, say they are pending.
- If checks are unavailable, state that explicitly and continue the code review using code evidence only.

CI results are evidence, not a substitute for review. Still verify correctness, design, and changed-code behavior from the actual diff and current files.

**Search callers when signatures change**: if the PR modifies a public function signature, model field, or URL name, find every caller and verify it was updated.

**Done when** CI state is reported or marked not applicable/unavailable, and signature/field/URL changes have caller evidence.

## Step 7 — Security Pass

Apply the Risk lens when the diff touches:

- `apps/user/**`, `apps/**/auth*` — authentication or permissions.
- `apps/api/**`, `**/api.py` — public API endpoints.
- `apps/**/forms*.py` handling file uploads.
- `config/**`, `**/settings*.py` — configuration.

If a security-review skill or checklist is available, apply it as complementary evidence; missing optional security skills are a review limitation, not an invented requirement.

**Done when** security-sensitive paths have been reviewed or explicitly marked not present.

## Step 8 — Verify Before Commenting

Before including any finding, confirm it in the actual code at the current commit, not just the diff. Keep Spec findings and Standards findings distinguishable until the final body; preserve both axes even when one is clean.

**Done when** every finding has current-code evidence, file/line when possible, and a clear axis: Spec, Standards/design, CI, or Security.

## Step 9 — Validate With User Before Posting

For PR reviews, present the full review content and wait for explicit confirmation before posting through any platform integration or API. For branch/WIP diff reviews, return the draft review and mark posting as not applicable unless the user provides a PR target.

Show:

- Full review body as it will appear on GitHub.
- Inline comments with file path and line number.
- Proposed event: `APPROVE`, `REQUEST_CHANGES`, or `COMMENT`.

Then STOP. Posting is a visible action that affects another developer's work.

**Done when** the user explicitly approves posting, asks for changes to the draft, or posting is marked not applicable.

## Output Format

**Language**: Spanish. All review comments and inline comments are written in Spanish. Code and identifiers stay in English.

**Tone**: Constructive throughout, including change requests. Explain the technical reason and give a concrete path forward.

### Structure

1. **Qué cambia** — one sentence.
2. **Spec / ajuste al problema** — verdict summary only: solved, partial, not solved, or unreviewable; mention missing/scope-creep categories without duplicating full findings.
3. **Standards / calidad de diseño** — verdict summary only: project-standard/domain/design status without duplicating full findings.
4. **Bloqueantes** — concrete findings requiring change. Each finding must include **qué**, **por qué**, and **cómo resolverlo**.
5. **Advertencias** — non-blocking but worth addressing.
6. **Checks de GitHub CI** — current check-run status when a PR exists, or not applicable/unavailable.
7. **Qué está bien** — brief acknowledgment of what was done well.

### Multi-round reviews

For re-reviews, first list what was resolved from the previous round, then list what still needs to change.

## References

- `references/test-review-quality.md` — test-review rules loaded when tests change.
- `references/migration-review-rules.md` — migration-review rules loaded when migrations change.
- `references/review-examples.md` — examples illustrating common review findings.

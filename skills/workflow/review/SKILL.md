---
name: review
description: "Review a pull request — verifies the change solves the stated problem, delegates domain rules to project skills, and checks design."
metadata:
  author: grupo-ilao
  version: "2.0"
---

## Purpose

Review pull requests as an orchestrator, not a rules container:

1. Does the change actually solve the stated problem?
2. Does it pass the project's domain rules (delegated to specialized skills)?
3. Does the design hold up (encapsulation, SRP, transactions, contracts)?
4. Do GitHub's CI checks for the PR pass?

This skill delegates domain rules to available project skills (`django-expert`, `django-pytest`, `htmx`, `huey`, `django-simplify`, `simplify`, `tailwind-4`, `alpinejs`, `django-components`) and project docs (`AGENTS.md`, `docs/agents/AGENTS.md`, `docs/`). One source of truth per domain — no duplication here. If a relevant skill is not installed, fall back to the repository docs and current code instead of inventing a missing skill requirement.

---

## Step 1 — Gather Context

**Fetch PR data** using whatever platform integration, CLI, or web context is available:
- title, description, author, and base branch
- list of changed files and diff stats
- inline comments and unresolved threads
- review history (APPROVED / CHANGES_REQUESTED / DISMISSED)

**Fetch linked issue context when available**: If the PR title contains an `ILA-\d+` Linear issue ID, use an available Linear integration or ask the user for the issue details. Pull the problem statement, acceptance criteria, and linked documents when possible. Use this as the "problem context" for Step 2.

If no Linear ID is present in the title, ask the user for the problem context before proceeding. Do not start a review without understanding what the PR is supposed to solve.

**Read `AGENTS.md`** at the repo root for the project map. Then prefer `docs/agents/AGENTS.md` as the agent-facing bootstrap/router for repo conventions. Follow the project-specific guides it points to for structural, style, pattern, and testing concerns based on what the PR touches.

**Previous review rounds**: If prior reviews exist, read all comments and verify each was addressed in the actual code — not just replied to in the thread. A DISMISSED review does not mean rejected; it may have been auto-dismissed by a new commit. Check the review's `commit_id` against the current HEAD before drawing conclusions.

When prior reviews reference inline comments, verify those were actually submitted via the GitHub API — not just mentioned in the review body.

---

## Step 2 — Verify the Solution Solves the Problem

Well-written code can still fail to fix the problem.

**Trace the full flow**: Follow the data from where it enters the system, through every layer it touches, to where it exits or is consumed. Verify that the fix operates at the layer where the root cause lives.

**Find the exit condition**: When something fails repeatedly, how does it leave the processing queue or retry loop? If there is no exit condition, the fix is incomplete regardless of how correct the individual code looks.

**Check the abstraction level**: If the problem lives in one layer but the fix is applied in a different one, the root cause is likely still present. A fix at the wrong layer is a workaround, not a solution.

**Ask**: Does the changed code remove the root cause, or does it add logic that coexists with the root cause while papering over the symptoms?

**Behavioral changes from replaced code**: When a PR replaces an existing property, method, or function, trace the behavioral difference between old and new. Even if the new behavior appears correct, surface it explicitly — the person merging needs to know that behavior X changed to Y, not just that the implementation changed.

---

## Step 3 — PR Size Heuristic

Before deep-diving into individual files, measure the PR:

- If additions > 500 lines OR files changed > 20, use that as an internal review risk signal and prioritize critical correctness/design findings.
- Do not include a PR-size warning by default. Mention size only when it materially prevents a reliable review or hides risk that the author can act on.

---

## Step 4 — Apply Project Standards via Delegation

Based on the file types touched, load and apply the relevant available project skills. Each skill is the canonical source for its domain — do not duplicate their rules in this review. If the runtime cannot load a listed skill, continue with `AGENTS.md`, `docs/`, and current code evidence.

### Routing by file type

| Path pattern | Skills to invoke |
|---|---|
| `apps/**/services*.py`, `apps/**/services/*.py` | `django-expert`, `django-simplify`, `simplify` |
| `apps/**/managers.py`, `apps/**/managers/*.py` | `django-expert`, `django-simplify` |
| `apps/**/views*.py`, `apps/**/forms*.py`, `apps/**/models*.py` | `django-expert`, `django-simplify`, `simplify` |
| `apps/**/*_tests.py`, `apps/**/tests/**/*.py` | `django-pytest` |
| `apps/**/tasks.py`, `apps/**/tasks/*.py` | `huey` |
| `apps/**/api.py`, `apps/**/api/*.py` | `django-expert` plus API docs/current code |
| `apps/**/migrations/*.py` | (manual rules — see below) |
| `**/*.html` with `hx-*` attributes | `htmx` |
| `**/*.html` with `x-data` / `x-bind` / `x-show` / `x-on` | `alpinejs` |
| `**/*.html`, `**/*.css` with Tailwind classes | `tailwind-4` |
| `components/**/*` | `django-components` |
| `tests/e2e/**/*.py`, `tests/e2e/**/*.ts` | available e2e/browser-testing guidance or manual review |

For any Python change, always additionally apply the project-wide coding standards routed from `docs/agents/AGENTS.md` or the repo's equivalent agent-facing project documentation router.

### Test review quality

When a PR adds or modifies tests, apply `django-pytest` as the source of truth and be strict about test quality. Do not treat the presence of a new test as sufficient coverage.

### Migration-specific rules (no dedicated skill)

- `RunPython` must provide `reverse_code` or explicit `RunPython.noop`
- Never import model classes inside `RunPython` — use `apps.get_model('app', 'Model')`
- `null=False` added to an existing column requires a two-step migration (add with default → backfill → drop default)
- Separate schema migrations from data migrations for easier rollback
- `on_delete=CASCADE` requires explicit justification — silent cascading deletes corrupt data
- `CREATE INDEX` on large tables should use `AddIndexConcurrently` to avoid locking writes
- `unique=True` added to an existing column requires a dedup migration first

---

## Step 5 — Design and Architecture

Beyond the domain rules applied in Step 4, apply these cross-cutting heuristics:

**Django model relationship changes**: When a PR adds or changes model relationships, invoke `django-expert` and `django-simplify`; apply their canonical relationship source-of-truth rules.

**Encapsulation violations**: Importing private symbols (prefixed with `_`) from another module signals misplaced responsibility. Either make the symbol explicitly public, or move it to a shared module.

**Single Responsibility violations**: A unit should have one reason to change. If two responsibilities will evolve independently in the future, split them now.

**Implicit contracts between modules**: Detecting conditions by parsing exception message strings creates a silent contract — a rename elsewhere breaks behavior with no type error. Use custom exception classes instead.

**Missing transaction boundaries**: Any service performing multiple writes, or catching `IntegrityError`, must use `@transaction.atomic`. Without it, a failed write in Postgres leaves the transaction aborted and silently fails all subsequent queries in the request.

**Inefficient bulk writes**: Writing inside a loop — one query per object — should become `bulk_create` / `bulk_update`.

**Missing abstraction**: When the same N values travel together across multiple function signatures, group them into a structure.

**Unreachable code**: A block that can never execute signals misunderstood control flow. Investigate before removing.

**Redundant control flow**: Statements the loop or block already performs implicitly signal unclear thinking.

**Behavior-preserving simplifications**: Actively look for improvements beyond correctness — unnecessary defensive code, costly operations that could be avoided, redundant intermediate variables, or logic that could be expressed more simply. Non-blocking unless the impact is significant, but always surface them.

### Project-specific blocking criteria

For IlaOS reviews, these are blocking unless the current diff proves they are harmless in that specific context:

- Temporary browser/debug statements left in production code (`console.log`, `console.debug`, `debugger`, or equivalent).
- Missing `transaction.atomic` around service operations that perform multiple related writes or combine writes with state transitions.
- Persisting timestamps with `timezone.localtime()` instead of `timezone.now()`; local conversion belongs in presentation code, not persisted state.

---

## Step 6 — Inspect GitHub CI Checks

Do **not** run tests, linters, type checkers, formatters, or project tooling locally as part of this review skill. The review validates automated checks against the PR's GitHub check runs / CI status.

Fetch the current GitHub checks for the PR head commit and report their state:
- If a check failed, quote the failing check name and summarize the failure from GitHub's check output or log snippet when available.
- If checks are pending, say they are pending; do not replace them by running local commands.
- If checks are unavailable or the platform integration cannot fetch them, state that explicitly and continue the code review using code evidence only.

CI results are useful evidence, but they do not replace the reviewer's job: still verify correctness, design, and changed-code behavior from the actual diff and current files.

**Search callers when signatures change**: If the PR modifies a public function signature, a model field, or a URL name, use available search tools to find every caller and verify they were updated. An unchanged caller of a changed signature is a broken reference the review must catch.

---

## Step 7 — Security Pass (conditional)

If the diff touches any of:

- `apps/user/**`, `apps/**/auth*` — authentication or permissions
- `apps/api/**`, `**/api.py` — public API endpoints
- `apps/**/forms*.py` that handle file uploads
- `config/**`, `**/settings*.py` — configuration

If a security-review skill or checklist is available, apply it for extra rigor. It is complementary to this review — use both when available, but do not block on a missing optional skill.

---

## Step 8 — Verify Before Commenting

Before including any finding in the review, confirm it in the actual code at the current commit — not just the diff. If something looks like a violation, read the file to verify it is still present. Technical claims that turn out to be wrong damage the credibility of the review.

---

## Step 9 — Validate With User Before Posting

Before posting through any platform integration or API, present the full review content to the user and wait for explicit confirmation.

Show:
- The full review body (all sections as they will appear on GitHub)
- Any inline comments, with file path and line number
- The proposed event (`APPROVE`, `REQUEST_CHANGES`, or `COMMENT`)

Then STOP and wait. Do not post until the user says to proceed. The user may want to remove findings, soften wording, change the verdict, or add context. This step is MANDATORY — posting a review is a visible action that affects another developer's work.

---

## Output Format

**Language**: Spanish. All review comments (body and inline) are written in Spanish. The team's working language for reviews is Spanish, even though code and identifiers are in English.

**Tone**: Constructive throughout — even when requesting changes. Frame as "acá conviene X porque Y", never "this is wrong with your code".

### Structure

1. **What the PR does** — one sentence
2. **Does it solve the problem?** — verdict first, reasoning after
3. **Blocking issues** — every finding is a three-part unit. All three elements are required:
   - **What** is wrong — the specific problem
   - **Why** it is wrong — the technical reason (broken contract, performance risk, layer violation, test contract gap, etc.)
   - **How to fix it** — a concrete direction or proposed solution. Sketch the implementation when possible — pointing at an abstraction is less useful than showing the path.

   Omitting any of the three produces incomplete feedback: "this is wrong" without a reason is unverifiable; a reason without a solution blocks the author without helping them move forward.
4. **Warnings** — non-blocking but worth addressing
5. **GitHub CI checks** — current check-run status; include failing check names and GitHub-provided failure details when available
6. **What is correct** — brief acknowledgment of what was done well

### Multi-round reviews

When this is a re-review, structure the body in two parts:
1. Explicitly list what was resolved from the previous round — the author deserves to see their work validated before reading what remains.
2. Then list what still needs to change.

Post using the available platform integration with the appropriate event (`REQUEST_CHANGES`, `APPROVE`, or `COMMENT`). Add inline comments on the specific diff lines for blocking issues when the line can be identified precisely.

---

## Examples

> The cases below illustrate the general rules above. They are real situations encountered in code reviews — not the rules themselves.

**Fix at the wrong abstraction level**: A service blocked individual documents via a JSON field on each document, but the processing queue filtered by the parent record. After the fix, the parent record kept re-entering the queue because the queue filter had no knowledge of the document-level state. Root cause: the fix was applied one layer below where the problem lived.

**Implicit cross-module contract**: A module detected a permanent failure by checking whether a specific phrase appeared in an exception message string. A rename of that message in another module would silently change behavior with no error surfaced. Correct approach: a custom exception class that makes the contract explicit and type-safe.

**Private symbol imported cross-module**: A function prefixed with `_` was imported from a sibling module. The prefix signals it is private to its module. Importing it externally means the responsibility is misplaced — the function should either be made explicitly public or extracted to a shared module.

**SRP violation in a service**: A form-submission service also contained logic to create related records from an AI cache. These are two separate concerns that change for different reasons. They belong in separate services, or the AI data should be passed as form initial data in the view so the user can confirm before anything is persisted.

**Comment thread resolved but code not updated**: A developer replied in a review thread that they had removed a piece of logic. The actual diff still contained it. Never trust the thread — verify the diff directly.

**Signature changed, caller not updated**: A service function added a required `agency` keyword argument. Grep found two callers unchanged — silent `TypeError` at runtime. Caught by the Step 6 grep-for-callers rule.

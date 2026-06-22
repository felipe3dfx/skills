---
name: prepare-commit
description: "Pre-commit quality gate — validate changed code, architecture, and test quality against AGENTS.md before staging; reports READY / NOT READY. Does not commit unless asked."
---

# Prepare Commit

## Activation Contract

Use when the user asks to prepare, validate, review, or finalize changes before a commit.
Use after implementation and before staging/committing.
If the change is managed under SDD, run the configured SDD verification flow first and then this skill.

## Hard Rules

- Do not commit, stage, amend, or push unless explicitly requested.
- Separate issues introduced by the current change from pre-existing repository debt; do not mix cleanup unless requested.
- Do not accept tests that only prove implementation plumbing.
- Prefer the smallest safe validation scope, but include every changed area.
- Use project-standard commands as documented in `AGENTS.md` (avoid introducing alternate command variants).

## Decision Gates

| Condition | Action |
|---|---|
| SDD is active for the change | Run the SDD verification flow first, then continue here. |
| Code changed | Run a `simplify` pass and the project's quality commands (per `AGENTS.md`). |
| Application logic changed | Check architecture and DRY/SRP against the project's standards (`AGENTS.md` and the topic docs it references). |
| Schema/data migrations changed | Run the project's migration/data checks (per `AGENTS.md`). |
| Tests changed | Validate test quality before trusting test results. |

## Execution Steps

1. Inspect `git status --short` and the full `git diff` for changed files.
2. Run a `simplify` pass on changed code: naming, structure, guard clauses, clarity, and unnecessary abstractions.
3. Validate architecture and implementation quality against the project's principles in `AGENTS.md` and the topic docs it references.
4. Check DRY/SRP in changed areas.
5. Review test quality (functional boundary-first, relevant scopes, no weak internal assertions).
6. Run the quality gates defined in `AGENTS.md` for the changed layers (e.g. lint/format/type checks for code, the test suite for tests).
7. Validate spacing/formatting checks for modified files (example: whitespace). See `AGENTS.md` for exact command forms.
8. Report final commit readiness with blockers, warnings, and exact commands run.

## Output Contract

Return:

- Verdict: `READY`, `READY WITH WARNINGS`, or `NOT READY`.
- Files reviewed.
- Issues found and whether fixed.
- Test-quality assessment.
- Commands run with pass/fail results.
- Pre-existing debt separated from current-change issues.

## References

- `AGENTS.md` — entry point for the project's architecture, testing, and quality rules, including the exact command forms.
- The topic docs `AGENTS.md` references (e.g. `docs/agents/*`) — coding standards, architecture patterns, and testing standards.

If the project has no `AGENTS.md`, fall back to the language's standard lint/format/test tooling and ask the user for any project-specific gates.

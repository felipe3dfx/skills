---
name: open-pr
description: Open a PR for this Django repo after the post-implementation gate passes. Issue-first: confirm ready-for-agent label before branching.
metadata:
  author: grupo-ilao
  version: "1.0"
---

## Purpose

Open a PR as an orchestrator, not a rules container. This skill owns the
PR-creation workflow and delegates every gate to the source that already owns
it — `AGENTS.md` for commands and gotchas, domain skills for cleanup, SDD for
verification. One source of truth per concern; no duplication here.

This repo does NOT use the upstream `branch-pr` conventions (`status:approved`,
`shellcheck`, `type:*` labels). Those belong to a different repo. Follow the
labels and commands below.

## Pre-flight: post-implementation gate

A PR is opened only after this gate passes on the exact commit that becomes the
PR head. If any edit is made after the gate, re-run it.

1. **Lint clean** — run the repo lint/format, then confirm clean:
   `uv run ruff check . && uv run djlint apps --check && pnpm exec biome check apps/core/static/js`
   (auto-fix via `uv run pre-commit run --files <changed-files>`; see `AGENTS.md`).
2. **Cleanup pass** — run `simplify` (Python) and `django-simplify` over the diff;
   for frontend touch `tailwind-4` / `htmx` / `alpinejs` as relevant.
3. **Tests pass** — capped to 2 threads, always: `uv run pytest -n 2`.
   Never run the unbounded default (see the parallelism + OOM warning in `AGENTS.md`).
4. **Verification binding** — if the change went through SDD, confirm the
   `sdd-verify` verdict was produced on this same HEAD, not an earlier state.
5. **Frontend built** — if assets changed, `pnpm run build` so
   `apps/core/static/css/dist/styles.css` is in sync.

## Workflow

```
1. Confirm the issue is linked and carries `ready-for-agent` (or ready-for-human if human work).
2. Branch off main: type/description  (feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert).
3. Commit with Conventional Commits — NO Co-Authored-By / AI attribution trailers.
4. Run the post-implementation gate above.
5. Push. The pre-push pytest hook is unbounded and can OOM the machine — run the
   capped suite manually first, then: git push --no-verify  (see AGENTS.md).
6. Open the PR with gh, using the body format below.
7. Apply repo canonical labels only (below). No `type:*`, no `status:approved`.
```

## PR body format

No `.github/PULL_REQUEST_TEMPLATE.md` exists; produce this structure:

- **Linked issue (required)** — `Closes #N` / `Fixes #N` / `Resolves #N`.
- **Summary** — 1–3 bullets of what the PR does.
- **Changes** — a `| File | Change |` table.
- **Test plan** — the exact gate commands run and their result. Do not claim
  tests passed unless you ran the command and report it (`AGENTS.md`).

## Labels

Use only the repo canonical labels (`docs/agents/triage-labels.md`):
`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.
The label lives on the **issue** as a readiness signal; this repo does not gate
the PR on a separate approval label.

## Oversized changes

If the diff is large enough to harm review focus (rule of thumb > 400 lines of
non-generated change), stop and split into chained PRs before opening — load the
`chained-pr` skill for the slicing strategy.

## Commands

```bash
git checkout -b feat/my-feature main
uv run pre-commit run --files <changed-files>   # auto-format + lint
uv run pytest -n 2                              # capped gate
git push -u origin feat/my-feature --no-verify  # pre-push hook is unbounded
gh pr create --title "feat(scope): description" --body "Closes #N

..."
```

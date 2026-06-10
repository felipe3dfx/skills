# 1. Replace gentle-ai `pr-review` with `grupo-ilao` `review`

Date: 2026-06-10

## Status

Accepted

## Context

The collection carried `pr-review` (and `branch-pr`), workflow skills derived
from [gentleman-programming/gentle-ai](https://github.com/gentleman-programming/gentle-ai).
`pr-review` was a rules-container review skill: it restated domain rules inline.

A newer review skill (`review`, authored by `grupo-ilao`, Apache-2.0) takes an
orchestrator approach instead — it routes each changed file to the canonical
domain skill (`django-expert`, `django-pytest`, `simplify`, etc.) and does not
duplicate their rules. One source of truth per domain.

## Decision

Remove `pr-review` and `branch-pr`. Adopt `review` as the single PR review
entry point. `repo-manager` now routes single-PR technical judgment to `review`.

`simplify` gains a **Delegated Mode** so it behaves correctly when `review`
delegates to it: scope to the PR diff, report findings (instead of editing in
place), and treat the delegation as explicit activation. Its standalone mode is
unchanged. This resolved a contract clash — `review` is read-only and validates
before posting, but standalone `simplify` edits files and refuses large diffs.

## Consequences

- Domain rules live in exactly one skill each; `review` composes them.
- Provenance and licensing changed: `review` is grupo-ilao / Apache-2.0, not
  gentle-ai. README credits and license notes updated accordingly.
- Any consumer relying on `pr-review` must switch to `review`.

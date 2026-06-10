# 2. Organize skills into category subdirectories

Date: 2026-06-10

## Status

Accepted

## Context

The `skills/` tree was flat — all 15 skills as direct children. The README,
however, already documented them in four groups (Django & backend, Frontend,
Testing, Workflow). The filesystem and the documented taxonomy had drifted:
the grouping existed only in prose.

[mattpocock/skills](https://github.com/mattpocock/skills) — a nested,
skills.sh-published collection — demonstrates that categorized paths
(`./skills/engineering/tdd`) work end to end, so nesting does not break
distribution.

## Decision

Move every skill under a category directory and mirror the README grouping:

- `skills/backend/` — django-expert, django-ninja, django-components,
  django-pytest, django-simplify, huey
- `skills/frontend/` — htmx, alpinejs, tailwind-4
- `skills/testing/` — pytest, playwright
- `skills/workflow/` — simplify, review, repo-manager, linear

`.claude-plugin/plugin.json` paths are updated to the categorized form, grouped
in README order and alphabetical within each category.

Add `scripts/`:
- `list-skills.sh` — asserts every plugin.json path resolves to a real
  `SKILL.md` and that no SKILL.md is left unregistered (CI-safe, exits non-zero
  on drift).
- `link-skills.sh` — symlinks skills into `~/.claude/skills` for live local
  testing. Non-destructive: it never deletes a real directory, only creates or
  re-points symlinks.

Empty staging dirs (`deprecated/`, `in-progress/`) and a `CONTEXT.md` glossary
were deliberately NOT added — they would imitate mattpocock's form without the
cause (his shape earned itself across ~28 skills and genuine domain ambiguity).
The `in-progress/` convention is documented in `AGENTS.md` instead.

## Consequences

- Filesystem now matches the documented taxonomy; new skills get a home by type.
- Distribution is the contract: discovery is driven by `plugin.json` paths, not
  a flat `skills/*` glob — so nesting is safe as long as `plugin.json` is kept
  in sync (now enforced by `list-skills.sh`).
- Skill cross-references are by `name`, not path, so the move required no edits
  inside any `SKILL.md`. Only `plugin.json` and `AGENTS.md` referenced paths.
- Consumers who installed via `npx skills` re-resolve from `plugin.json`; no
  action needed on their side.

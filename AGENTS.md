# Repository guide

This repo is a **collection of LLM-first agent skills** — not an application. There is no build, no test runner, and no lint step for the repo itself. The content is Markdown (`SKILL.md` files) plus a handful of standalone Python audit scripts that the skills run against a *target* project, never against this repo.

Published two ways from the same `skills/` tree:
- **Claude Code plugin** — `.claude-plugin/plugin.json` lists each skill by directory path. This file is the discovery contract: distribution reads the declared paths, not a flat glob, so nesting is fine as long as plugin.json stays in sync.
- **skills.sh** — `npx skills@latest add felipe3dfx/skills` copies skills as real files into the consumer's agent skills directory.

## Layout

Skills are grouped into category subdirectories that mirror the README table:
- `skills/backend/` — Django & backend (`django-expert`, `django-ninja`, `django-components`, `django-pytest`, `django-simplify`, `huey`).
- `skills/frontend/` — `htmx`, `alpinejs`, `tailwind-4`.
- `skills/testing/` — `pytest`, `playwright`.
- `skills/workflow/` — `simplify`, `review`, `repo-manager`, `linear`.

A new skill goes in the category that matches its domain. A skill that is not ready to publish lives under `skills/in-progress/` and is left out of `plugin.json` until it ships — there is no empty placeholder dir for this; create it when you first need it. Retired skills are deleted (git keeps the history), not kept as a graveyard.

`scripts/` holds repo tooling (not shipped to consumers):
- `scripts/list-skills.sh` — asserts every `plugin.json` path resolves to a real `SKILL.md` and that no `SKILL.md` is left unregistered. Exits non-zero on drift, so run it after any add/move/remove. This is the restructure safety net.
- `scripts/link-skills.sh` — symlinks skills into `~/.claude/skills` for live local testing. Non-destructive: it never deletes a real directory, only creates or re-points symlinks.

`docs/adr/` holds Architecture Decision Records — numbered, append-only. Add one when a decision is worth explaining later (see `0001`, `0002`).

## Skill anatomy

Each skill is one directory under `skills/<category>/<dir>/` containing:
- `SKILL.md` — required. YAML frontmatter (`name`, `description`, sometimes `license`, `metadata`, `trigger`) followed by the instructions the agent loads.
- `references/` — optional deep-dive docs loaded on demand, not upfront. Keep the `SKILL.md` lean and push detail here (see `backend/django-expert/references/`).
- `scripts/` — optional standalone Python AST-based audit tools the skill invokes on a target codebase (see `backend/django-simplify/scripts/`, `backend/django-pytest/scripts/`). Run via `python <script>.py <path> --json`; they have no repo-level dependencies.
- `assets/` — optional templates (see `workflow/linear/assets/`).

## Editing rules that span multiple files

- **Adding, moving, or removing a skill touches two sources of truth that must stay in sync**: `.claude-plugin/plugin.json` (grouped by category in README order, alphabetical within) and the skill table in `README.md`. After any such change, run `scripts/list-skills.sh` to prove they still agree.
- **Directory name ≠ skill name.** `plugin.json` and `npx skills` key on the *directory*, but the agent loads the `name:` from frontmatter. They usually match — one deliberate exception: `skills/workflow/linear/` declares `name: create-linear-comment`. Do not "fix" this by renaming without checking the README and plugin references.
- **Cross-skill references are by `name`, not path** (e.g. `review` routes to `django-expert`). Moving a skill between categories therefore needs no edits inside any `SKILL.md` — only `plugin.json` and this file reference paths.
- **Licensing is repo-wide.** The whole collection is covered by the root MIT `LICENSE`; skills do not declare their own `license:` in frontmatter. Do not add one — provenance/attribution belongs in the README Credits section, not in per-skill license fields.

## Skill-orchestration architecture

A few skills are orchestrators that delegate to domain skills rather than duplicating rules — one source of truth per domain:

- **`review`** (PR code review) is the top orchestrator. Step 4 routes each changed file by type to the canonical domain skill (`django-expert`, `django-pytest`, `htmx`, `alpinejs`, `tailwind-4`, `django-components`, `simplify`, `django-simplify`). It does not restate their rules. Output is read-only findings (what / why / how) and it validates with the user before posting anything.
- **`repo-manager`** handles multi-PR/issue coordination and routes single-PR technical judgment to `review`.
- **`simplify`** has a **Delegated Mode** (invoked by `review`): when delegated it scopes to the PR diff, reports findings in Spanish instead of editing in place, and skips its standalone activation guards. Its default standalone mode still edits files directly. Keep these two contracts distinct when editing it.

When changing an orchestrator's routing or a domain skill's scope, check the counterpart so the delegation contract stays consistent (e.g. `review`'s routing table vs. each delegate's "When to Use" / output mode).

## Conventions

- **Review output language is Spanish** (`review`, and `simplify`'s Delegated Mode findings). Code, identifiers, and the skills themselves stay in English.
- `.atl/` is a local skill-registry cache — gitignored, not documentation.

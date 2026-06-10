# 3. Unify all skills under the repo-level MIT license

Date: 2026-06-10

## Status

Accepted

## Context

Ten skills declared `license: Apache-2.0` in their `SKILL.md` frontmatter while
the repository's root `LICENSE` is MIT. The per-skill fields shadowed the
general license and made the licensing story inconsistent: most of those ten had
no attached author and were the maintainer's own work; one (`review`) is
third-party (authored by `grupo-ilao`, originally Apache-2.0).

The risk was raised explicitly: Apache-2.0 requires preserving the license and
attribution when redistributing third-party work, so stripping `review`'s
license field carries an attribution-compliance risk. The maintainer accepted
that and chose to unify everything under the repo MIT license.

## Decision

Remove the `license:` frontmatter field from all skills. The root MIT `LICENSE`
governs the entire collection. Provenance and attribution stay in the README
Credits section (prose), not in per-skill license fields — `review` is still
credited to `grupo-ilao` and `repo-manager` to gentle-ai there.

`AGENTS.md` now instructs maintainers not to add per-skill `license:` fields.

## Consequences

- One licensing source of truth: the root MIT `LICENSE`.
- Attribution for third-party-derived skills is documentary (README Credits)
  rather than enforced via a frontmatter license header. For `review` this is a
  deliberate, accepted divergence from the upstream Apache-2.0 redistribution
  terms — revisit if the collection is ever redistributed formally.

# Migration Review Rules

Use this reference when a PR touches `apps/**/migrations/*.py` or equivalent Django migration paths.

## Rules

- `RunPython` must provide `reverse_code` or explicit `RunPython.noop`.
- Never import model classes inside `RunPython`; use `apps.get_model('app', 'Model')`.
- Migration code must be self-contained and must not depend on mutable runtime helpers/constants for business mappings. Migrations are historical artifacts.
- `null=False` added to an existing column requires a two-step migration: add with default → backfill → drop default.
- Separate schema migrations from data migrations for easier rollback.
- `on_delete=CASCADE` requires explicit justification.
- `CREATE INDEX` on large tables should use `AddIndexConcurrently` to avoid locking writes.
- `unique=True` added to an existing column requires a dedup migration first.

## Completion criterion

Done when every migration file has been checked against these rules and any rollback, locking, historical-dependency, or data-safety risk is reported with the migration file path.

# Test Review Quality

Use this reference when a PR adds or modifies tests. `django-pytest` remains the source of truth for Django test style; these rules focus on review judgment.

## Blocking test problems

Tests that only assert implementation wiring are blocking when they replace meaningful behavioral coverage.

Examples of implementation-detail tests:

- asserting a field is or is not a relation when the business behavior is what matters;
- asserting exact enum numeric values instead of accepted/rejected domain values;
- asserting admin class membership without proving an admin workflow;
- asserting CSS media strings or internal widget details without proving user-visible behavior;
- asserting internal `select_related` dictionaries without proving the queryset returns the right business records.

## Preferred evidence

Prefer functional/regression tests that protect observable contracts inside PR scope:

- form/admin submissions persist expected records;
- duplicate constraints reject invalid states;
- querysets/managers return the right business records;
- user-facing validation errors appear when they are part of the UX;
- regression tests fail on the previous bug and pass with the current change.

## Completion criterion

Done when every new or changed test is classified as behavioral coverage, implementation-detail coverage, or irrelevant to the changed behavior, and any blocking replacement of meaningful behavior coverage is reported.

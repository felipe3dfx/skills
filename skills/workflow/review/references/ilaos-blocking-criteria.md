# IlaOS Blocking Criteria

Use this reference for IlaOS PR reviews after applying domain skills and general design heuristics.

These findings are blocking unless the current diff proves they are harmless in context.

## Blocking criteria

- Temporary browser/debug statements in production code: `console.log`, `console.debug`, `debugger`, or equivalent.
- Missing `transaction.atomic` around service operations with related writes or write/state-transition combinations.
- Persisting timestamps with `timezone.localtime()` instead of `timezone.now()`; local conversion belongs in presentation code.
- Persisting domain enums as numeric `IntegerField` choices; use readable string slugs (`SlugField` with `TextChoices`).
- Replacing an existing domain entity relationship with an enum when the domain already has a canonical model.
- Heavy Django admin UI customization with custom CSS/forms/widgets that moves admin away from stock Django patterns; keep admin operational and simple, and build product-grade UI outside admin.

## Completion criterion

Done when every applicable blocking criterion has been checked against the current diff and any finding explains why it is harmful in this PR's context.

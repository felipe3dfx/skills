# Review Examples

These examples illustrate the review rules in `../SKILL.md`. They are not additional rules.

## Fix at the wrong abstraction level

A service blocked individual documents via a JSON field on each document, but the processing queue filtered by the parent record. After the fix, the parent record kept re-entering the queue because the queue filter had no knowledge of the document-level state.

Root cause: the fix was applied one layer below where the problem lived.

## Implicit cross-module contract

A module detected a permanent failure by checking whether a specific phrase appeared in an exception message string. A rename of that message in another module would silently change behavior with no error surfaced.

Correct approach: use a custom exception class that makes the contract explicit and type-safe.

## Private symbol imported cross-module

A function prefixed with `_` was imported from a sibling module. The prefix signals it is private to its module. Importing it externally means the responsibility is misplaced.

Correct approach: make the function explicitly public or extract it to a shared module.

## SRP violation in a service

A form-submission service also contained logic to create related records from an AI cache. These are separate concerns that change for different reasons.

Correct approach: split them into separate services, or pass the AI data as form initial data in the view so the user can confirm before anything is persisted.

## Comment thread resolved but code not updated

A developer replied in a review thread that they had removed a piece of logic. The actual diff still contained it.

Correct approach: never trust the thread alone. Verify the current code directly.

## Signature changed, caller not updated

A service function added a required `agency` keyword argument. Caller search found two callers unchanged, creating a runtime `TypeError` risk.

Correct approach: search all callers when public function signatures, model fields, or URL names change.

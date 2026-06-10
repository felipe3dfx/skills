# Create QA Comment for Linear Issues

This reference guide describes how to create comprehensive QA comments for Linear issues.

## Scope and Boundaries

- This workflow is for **QA-oriented communication** to QA/PM/PO.
- It summarizes observable behavior and test guidance.
- It does **not** replace technical code review, root-cause analysis, or architecture review.

## Required Inputs

Before drafting, confirm all required inputs:

1. **Linear issue ID** (e.g., `BUG-123`)
2. **Commit references** (one or more), accepted formats:
   - Commit SHA (`a1b2c3d` or full SHA)
   - Commit range (`a1b2c3d..d4e5f6g`)
   - Branch name (`feature/x`)
   - PR URL (`https://github.com/org/repo/pull/123`)

If inputs are missing, conflicting, or ambiguous, **stop and ask** before continuing.

## Process Overview

You are drafting a Linear issue comment aimed at non-technical teammates (QA, PM, PO). Follow this process:

1. Use the runtime-available Linear tools to fetch issue details for `$issue_id`. Capture title, description, acceptance criteria, QA notes, related issues, relevant labels, and the primary language used in the issue.
2. For each commit reference supplied in `$commits`, collect the summary and the key changes that affect user-facing behaviour. Analyze the commits to identify:
   - User-visible changes (UI, features, behavior)
   - Database migrations or schema changes
   - API contract changes or breaking changes
   - Environment variable or configuration requirements
   - Performance or security implications
   - Dependencies on other issues or PRs
   Describe resulting changes without exposing unnecessary internals. If a reference cannot be resolved or maps to multiple candidates, stop and ask.
3. Align the implemented changes with the user-facing requirements from the issue. Emphasize how each requirement is satisfied from the stakeholder perspective.
4. Determine the comment language from the issue itself:
   - Match the primary language used in the issue title/description and stakeholder-facing notes.
   - If the issue mixes languages, follow the dominant stakeholder-facing language.
   - Keep code identifiers in their original language regardless of the issue language.
   - If the intended language is still unclear, stop and ask before drafting.
5. Select the template **before drafting** using the rules below.
6. Define test scenarios that a QA reviewer should execute, with depth based on the selected template:
    - Happy path scenarios (positive cases)
    - Edge cases and boundary conditions
    - Negative scenarios (error handling, validation)
    - Regression test reminders for related areas
    Each scenario must describe user-visible behaviour, list the key steps to perform, specify any test data requirements, and state the expected result using impersonal phrasing.
7. Identify any breaking changes, deployment requirements, rollback procedures, or dependencies that need to be communicated.
8. Compose a concise Markdown **draft** following the selected template and the issue's language. Include only relevant sections.
9. **Mandatory publish-safety gate**:
    - Always show the draft to the user first.
    - Always ask for explicit approval before publishing.
    - If approval is not explicit, do not publish.
10. After approval, publish using the runtime-available Linear comment capability and confirm success.
11. If a critical requirement is not addressed by available evidence, inform the user and ask whether to proceed.

## Template Selection Rules

### Use `comment-template-simple.md` when **all** conditions are true

- Scope is localized: one primary behavior/flow, or tightly related behavior in a single area.
- Risk is low and no broad edge-case matrix is expected.
- No major dependencies: no coordinated rollout/order constraints and no critical cross-ticket blockers.
- No migration/configuration/feature-flag/API-contract concern that must be coordinated with QA/PM.
- Regression surface is narrow (one primary area plus small adjacent impact).
- Validation fits in a short checklist (a few checks).

### Use `comment-template-detailed.md` when **any** condition is true

- Multiple behaviors/flows changed, or changes span more than one user journey.
- Important edge cases/negative paths require explicit planning.
- Dependencies or release sequencing must be coordinated.
- Migration, configuration, flag, compatibility, or environment concerns exist.
- Regression risk spans multiple related areas.

### Ambiguity default

If evidence is mixed or incomplete, start with `comment-template-simple.md` unless at least one detailed trigger is clearly confirmed.

## Template Structure

Use one of the following templates based on selection rules:

- [assets/comment-template-simple.md](../assets/comment-template-simple.md)
- [assets/comment-template-detailed.md](../assets/comment-template-detailed.md)
- [assets/comment-template.md](../assets/comment-template.md) (selector overview)

See [preferences.md](preferences.md) for language guidelines and writing preferences.

## Quality Checklist

Before finalizing:

- Double-check the consistency between the issue requirements and the listed changes.
- Ensure each test case maps to a described change and covers happy path, edge cases, and regression scenarios.
- Verify that breaking changes, dependencies, and deployment requirements are clearly communicated.
- Confirm that the selected template matches the assessed risk/scope criteria.
- Omit optional sections (Deployment & Environment, Dependencies, Breaking Changes, Rollback Plan, Visual Evidence) if they are not applicable to avoid cluttering the comment.
- Ensure test cases are specific, actionable, and include test data requirements when needed.
- Ensure prose matches the primary language of the Linear issue, while code identifiers remain in their original language.
- Avoid unsupported claims; when evidence is missing, state uncertainty clearly.
- Confirm publication only after explicit approval and successful tool execution.

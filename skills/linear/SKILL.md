---
name: create-linear-comment
description: Draft a Markdown Linear comment aligned with issue requirements and commits. Creates comprehensive QA comments for Linear issues with test scenarios, dependencies, and technical notes. Use when creating QA comments for Linear issues or when documenting implementation changes for non-technical teammates.
---

# Create Linear QA Comment

This skill drafts **QA-oriented Linear comments** for non-technical teammates (QA, PM, PO) based on issue requirements and commit evidence.

## Scope and Boundaries

- ✅ In scope: summarize observable behavior changes, propose QA scenarios, and communicate dependencies/risks for release coordination.
- ❌ Out of scope: replacing technical code review, architecture validation, or root-cause analysis.
- If root-cause or deep technical review is required, stop and ask the user to run a dedicated review workflow first.

## Quick Start

1. Provide the Linear issue ID (e.g., `BUG-123`).
2. Provide at least one commit reference (or confirm no-commit mode).
3. The skill drafts a structured QA comment.
4. **Safety gate (mandatory):** show draft first and request approval before publishing.

Accepted commit references:
- Commit SHA: `a1b2c3d` (short) or full SHA
- Commit range: `a1b2c3d..d4e5f6g`
- Branch name: `feature/checkout-fix`
- PR URL: `https://github.com/org/repo/pull/123`

If inputs are missing or ambiguous, **stop and ask** before drafting.

## Detailed Process

See [references/create-qa-comment.md](references/create-qa-comment.md) for the complete process and guidelines.

## Project Preferences

This skill uses project-specific preferences for language and template format:

- **Language**: Match the primary language of the Linear issue (title, description, and stakeholder context). See [references/preferences.md](references/preferences.md) for language settings and writing guidelines.
- **Templates**:
  - [assets/comment-template-simple.md](assets/comment-template-simple.md) for localized/low-risk changes
  - [assets/comment-template-detailed.md](assets/comment-template-detailed.md) for higher-risk or cross-flow changes
  - [assets/comment-template.md](assets/comment-template.md) for quick selector guidance

## Template Selection Rules (Mandatory Before Drafting)

Choose the template **before writing the draft**.

Use the **simple template** only when all are true:
- The change is localized to one behavior/flow (or tightly related behavior in the same area).
- Risk is low and no significant edge-case matrix is expected.
- No major dependencies (no blocking issues, coordinated rollout, or sequence-sensitive release steps).
- No migration/config/flag/API contract concern that QA/PM must coordinate.
- Regression surface is narrow (single primary area).
- Validation can be covered with a few checks.

Use the **detailed template** when any of these is true:
- Multiple behaviors/flows were touched.
- Important edge cases or negative paths must be coordinated.
- There are dependencies, rollout/order concerns, or cross-ticket coordination needs.
- There are configuration, migration, flag, or compatibility considerations.
- Regression risk affects multiple related areas.

**Ambiguity default**: start with the simple template unless context clearly meets any detailed trigger.

## Usage

The skill follows this workflow:

1. Fetch issue details using runtime-available Linear tools
2. Analyze commits for user-facing changes
3. Align changes with issue requirements
4. Select the template (simple vs detailed) using explicit decision rules
5. Generate test scenarios with depth appropriate to the selected template
6. Identify breaking changes and dependencies
7. Compose a draft comment
8. Show the draft and request approval
9. Publish only after explicit user approval

Refer to the [reference guide](references/create-qa-comment.md) for detailed instructions, [preferences](references/preferences.md) for language guidelines, and [comment template](assets/comment-template.md) for the template structure.

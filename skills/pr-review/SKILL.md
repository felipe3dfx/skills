---
name: pr-review
description: >
  Technical review skill for a single PR/MR to verify whether changes solve the
  underlying problem safely and correctly end to end.
  Trigger: When user asks to review one specific PR/MR implementation or prepare
  technical review feedback for that change.
license: Apache-2.0
metadata:
  version: "2.0"
---

## When to Use

Use this skill only when evaluating the technical correctness of **one PR/MR**.

Typical triggers:
- "Review this PR/MR"
- "Does this change actually fix the bug?"
- "Help me draft review feedback for this PR"

If the task is backlog triage, multi-PR sequencing, issue listing, or repository operations, use **`repo-manager`**.

## Goal

Deliver a problem-first review that answers:
1. Is the underlying problem understood?
2. Does this PR/MR solve the root cause end to end?
3. Is it safe to ship under this repository's standards?

## Non-negotiable Rules

1. **No review without problem context.** If issue/goal is unclear, stop and ask.
2. **Verify root cause and full flow, not style in isolation.**
3. **Load repo skills/docs first** and use them as primary review criteria.
4. **Read current code, not only the diff.**
5. **If contracts/signatures change, check callers/consumers.**
6. **Discover and run real repo checks** (do not assume commands).
7. **Run security pass only when risk justifies it.**
8. **Verify every claim before commenting publicly.**
9. **Show full draft, then explicitly stop for confirmation before posting.**

## Review Workflow

### Phase 1) Gather mandatory context

Collect:
- PR/MR metadata and scope (files, stats, commits)
- Linked issue/ticket and acceptance criteria
- Existing comments/threads and current review state

If problem context is missing: **stop and request it**.

### Phase 2) Size gate and review depth

- **S**: up to ~200 net lines
- **M**: 200–600
- **L**: 600–1200
- **XL**: >1200 or mixed domains

For L/XL, explicitly warn about review risk and recommend split/phased review.

### Phase 3) Load repository standards first (mandatory)

Before judging code quality:
1. Read `AGENTS.md` and repository docs
2. Load relevant project/custom skills by changed-file domain
3. Fall back to generic best practices only when no repo guidance exists

### Phase 4) Build baseline from current code

Read the current implementation around the diff:
- Entry points and affected modules
- Related services/adapters/models/components
- Existing tests and expected behavior

### Phase 5) Validate problem → solution

For each important change, verify with evidence:
1. Expected root cause
2. Whether change addresses cause vs symptoms
3. End-to-end flow coverage (input, validation, persistence, output, error path)
4. Edge cases left uncovered

### Phase 6) Contract and caller impact

If signatures/contracts/routes/events/payloads changed:
- Find callers/consumers
- Confirm all usages were adapted
- Confirm tests/docs updated where applicable

### Phase 7) Repository checks (discovered, not assumed)

Discover official checks from repo tooling (e.g., Makefile/just/CI/manifests), then run relevant ones:
- tests
- lint/format/type checks
- build/check commands as applicable

Report any skipped checks and why.

### Phase 8) Conditional security pass

Perform security-focused review when touching sensitive areas (auth, permissions, secrets, PII, payments, uploads, dynamic query/command construction, external integrations).

### Phase 9) Verify findings before drafting comments

Every finding must be backed by current evidence in code/tests/config/runtime artifacts.
If uncertain, mark as hypothesis and ask for evidence.

### Phase 10) Draft review and explicit stop

Draft full review in language based on this order:
1. User explicit preference
2. Repository/team convention
3. PR/MR author language

Then stop with explicit confirmation, e.g.:

> "This is the full draft review. Do you want me to publish it as-is?"

Do not post without explicit approval.

## Universal Red Flags

Treat as blocking unless disproven:
- Claimed bug fix does not address root cause
- Contract change without caller updates
- Missing or misleading tests for changed behavior
- Silent breaking change without migration/compatibility plan
- Hardcoded secrets/credentials or unsafe secret handling
- Security-sensitive path changed without appropriate guards

## Verdict Policy (Decision Matrix)

| Verdict | When to use |
|---|---|
| **Approve** | Problem is solved end to end, risk is acceptable, checks pass or justified |
| **Request changes** | Blocking issues exist that affect correctness/safety/contracts |
| **Comment** | Non-blocking suggestions or clarifications only |

## Comment Style

- Concise, human, direct
- Lead with numbered findings
- For each finding: **problem** → short evidence → concrete fix
- No unnecessary fluff, no generic praise padding
- End with brief acknowledgement of what is correct (when genuine)

## Example Review Messages

### Approve

```text
Root cause is addressed end to end, caller contracts remain compatible, and checks passed. Approved.
```

### Request changes

```text
Two blocking issues:
1. **Contract break in payload shape** — `createOrder()` now requires `currency`, but two existing callers still send the old shape. Update callers or add backward-compatible handling.
2. **Root cause only partially fixed** — input validation was added, but the failing async retry path still bypasses it. Apply the same guard in the worker path and add coverage.

What is solid: tests for the sync path are clear and the error messages improved.
```

### Comment (non-blocking)

```text
Looks correct for the target bug. One suggestion: add a focused regression test for the null-id edge case so this behavior stays protected.
```

## Platform Neutrality

This methodology applies to GitHub, GitLab, Bitbucket, and similar systems. Adapt commands/tooling to the repository environment; do not assume a specific provider.

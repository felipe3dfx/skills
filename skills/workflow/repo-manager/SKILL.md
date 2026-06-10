---
name: repo-manager
description: >
  Repository and collaboration-platform operations skill for PRs/MRs, issues, branches,
  backlog hygiene, and review orchestration across providers.
  Trigger: When user asks to manage repository workflows, coordinate reviews, triage work,
  or run platform-level contribution operations.
metadata:
  version: "1.0"
---

## When to Use

Use this skill for repository/platform operations, for example:
- Listing and triaging PRs/MRs/issues
- Backlog hygiene and prioritization
- Branch/release workflow coordination
- Review orchestration (who reviews what, in what order)
- Cross-PR dependency/conflict coordination
- Preparing, routing, or executing platform actions

If the task is to **technically judge whether one specific PR/MR is correct and solves the problem**, invoke **`review`**.

## Scope and Boundaries

### Owns
- Repository-level coordination and workflow management
- Platform operations (open/update/label/assign/comment/merge/close)
- Multi-item planning (many PRs/MRs/issues at once)
- Review queue and merge-order management

### Does NOT own
- Deep technical correctness review of a single PR/MR implementation
- Root-cause validation and end-to-end flow verification inside one code change

For those, route to **`review`**.

## Operating Principles

1. **Provider-aware, not provider-locked**: adapt to GitHub/GitLab/Bitbucket or equivalent tooling in the repo.
2. **Context first**: understand goals, constraints, branch policy, and release pressure before taking actions.
3. **Safety first**: avoid destructive operations unless explicitly requested.
4. **Traceability**: link actions to issue/ticket context where possible.
5. **Clear handoffs**: when delegating a single PR/MR technical judgment, pass context to `review`.

## Workflow

### 1) Clarify Objective
- What outcome is needed? (triage, cleanup, merge plan, review routing, release prep)
- What platform/provider is in use?
- What constraints apply? (freeze windows, required checks, approval rules)

### 2) Gather Repository State
- Fetch PR/MR and issue lists with status, assignee, labels, age, and blockers.
- Identify stalled items, missing metadata, and dependency chains.
- Detect possible merge conflicts and ordering risks across multiple changes.

### 3) Classify and Orchestrate
- Group items by urgency/risk/impact.
- Propose merge or review order with rationale.
- Route single-change technical evaluation requests to `review`.

### 4) Execute Platform Operations
- Perform requested non-destructive operations first (labels, comments, assignments, status updates).
- For impactful actions (merge/close/reopen), confirm intent when policy requires.
- Record what was done and what remains.

### 5) Report
- Provide concise summary: actions taken, open risks, next recommended steps.

## Delegation Contract to `review`

When escalating one PR/MR for technical judgment, include:
- PR/MR identifier and base/head
- Linked issue/task and acceptance criteria
- Noted risks or suspected root cause
- Any branch policy or review constraints

Expected output from `review`: approve/request-changes/comment recommendation backed by evidence.

## Example Commands (illustrative only)

These are examples; use the provider/tooling actually available in the repository.

```bash
# GitHub examples
gh pr list --state open
gh issue list --state open

# GitLab examples
glab mr list
glab issue list

# Bitbucket examples (via API/CLI wrappers)
# bb pr list
# bb issue list
```

## Output Template

```markdown
## Repository Management Summary
- Objective: ...
- Platform: ...

## Actions Taken
1. ...
2. ...

## Review Orchestration
- Routed to review: <PR/MR>
- Pending review: ...

## Risks / Blockers
- ...

## Recommended Next Steps
1. ...
2. ...
```

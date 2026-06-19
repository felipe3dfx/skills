# Comment Template Selector

Use this file only to choose the correct template. For full structure, use one of these:

- [comment-template-simple.md](./comment-template-simple.md)
- [comment-template-detailed.md](./comment-template-detailed.md)

Decision rule summary:

- Choose **simple** when the change is localized, low-risk, has no major dependencies, and the comment fits in: brief summary + ~1–3 actionable checks with little to no coordination burden.
- Choose **detailed** when there are **more than 3 meaningful checks** or the change has broader risk, dependencies, edge cases, rollout concerns, or cross-team coordination needs.
- If ambiguous, default to **simple** unless a detailed trigger is clearly confirmed.

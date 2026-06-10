# QA Comment Template — Detailed

Use for higher-risk, multi-flow, or coordination-heavy changes.

```markdown
## ✨ Summary
- {Describe the change and its functional impact}
- {Clarify the visible scope for QA/PM}
- {State what QA should validate first as the top priority}

## 🧭 Areas / Impacted Flows
- {Flow/area 1}
- {Flow/area 2}

## ✅ Suggested Test Plan
<!-- Include only checks that affect QA/release decisions; avoid filler -->

### Main Flow
- [ ] {Primary happy-path case}
  - **Steps**
    1. {Step 1}
    2. {Step 2}
  - **Test data**: {required data}
  - **Expected result**: {observable result}

### Edge Cases and Negative Paths
- [ ] {Critical edge case or validation}
  - **Steps**: {steps}
  - **Expected result**: {expected validation/error handling}
- [ ] {Second relevant edge/negative case}

### Recommended Regression
- [ ] {Related area 1}
- [ ] {Related area 2}
- [ ] {Relevant integration or cross-flow}

## 🔗 Dependencies and Coordination
- {Related issue/PR/deploy}
- {Deployment order or prerequisite, if applicable}

## ⚠️ Release Risks and Considerations
- {Functional or compatibility risk}
- {Required configuration/flag/migration, if applicable}

## ❓ Open Questions or Uncertainties
- {What could not be confirmed with the available evidence}

<!-- Optional: include only when it affects decision-making -->
## 🔄 Contingency
- {Recommended action if validation finds a failure}
```

Guidelines:
- Prioritize QA/PM coordination: what to validate, where the risk is, and what depends on what.
- Avoid implementation detail that is not needed for validation or release decisions.

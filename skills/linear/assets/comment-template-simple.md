# QA Comment Template — Simple

Use for localized, low-risk changes where validation fits in a short checklist.

```markdown
## ✨ Summary
- {Describe the main observable change for the end user}
- {Add brief impact in QA/PM-friendly language}

<!-- Optional: include only when QA needs context to run validation -->
## 🧩 Preconditions
- {Required role/profile}
- {Environment/flag/minimum data required}

## ✅ What to Validate
- [ ] {Primary happy-path check}
- [ ] {Key edge-case or error check}
- [ ] {Short regression check in a related area}

<!-- Optional: only if a specific check needs more precision -->
<!-- Place below the specific checklist item that needs it -->
  - **Steps (if needed)**: {1-3 steps max}
  - **Expected result (if needed)**: {observable result}

<!-- Optional: include only if relevant -->
## 🔗 Coordination Note
- {Specific dependency or release consideration, if any}
```

Guideline:
- Maximize clarity and validation speed.

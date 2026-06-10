# Project Preferences

This reference file contains project-specific preferences and configurations for creating Linear QA comments.

## Language Settings

- **Primary Language**: Match the primary language of the Linear issue
- **Tone**: Neutral, concise, QA/PM-friendly changelog style
- **Code Identifiers**: Keep in original language (identifiers, branch names, API names, labels)

## Writing Guidelines

- Use neutral phrasing throughout (avoid first-person references)
- Write all user-facing prose in the same primary language as the Linear issue
- Keep code identifiers in their original language (do not translate names)
- Prefer direct, concise changelog phrasing (e.g., "Updated...", "Fixed...", "Added...")
- Prioritize observable behavior and QA impact over implementation internals
- Do not claim validation, coverage, performance, or impact unless evidence is available
- If evidence is missing, state uncertainty explicitly in the issue language (e.g., "Could not confirm..." / "No se pudo confirmar...")
- If the issue mixes languages, follow the dominant stakeholder-facing language; if still unclear, ask before drafting

## Examples

✅ Good:
- "Updated the search flow so it now shows paginated results."
- "Fixed the save error when the `email` field is empty."
- "Could not confirm performance impact with the available evidence."
- "Se actualizó el flujo de búsqueda y ahora muestra resultados paginados." (when the issue is in Spanish)

❌ Bad:
- "I implemented the feature..." (first person)
- "We added validation..." (first person plural)
- "Validated that there are no regressions" (unsupported claim if not verified)
- "Updated the flow..." on a Spanish issue without a clear reason to switch languages

## Comment Templates

Use the template selected by the workflow rules in `create-qa-comment.md`:

- [assets/comment-template-simple.md](../assets/comment-template-simple.md) for localized/low-risk changes
- [assets/comment-template-detailed.md](../assets/comment-template-detailed.md) for broader/higher-risk changes
- [assets/comment-template.md](../assets/comment-template.md) for quick selector guidance

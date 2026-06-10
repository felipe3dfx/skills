# Skills

[![skills.sh](https://skills.sh/b/felipe3dfx/skills)](https://skills.sh/felipe3dfx/skills)

Custom [agent skills](https://www.skills.sh/docs) for AI coding assistants — focused on Django, modern frontend (HTMX, Alpine.js, Tailwind 4), testing with pytest, and PR/issue workflows. Built for Claude Code and OpenCode, but model-agnostic.

## Install

```bash
npx skills@latest add felipe3dfx/skills
```

Pick the skills you want and the agents to install them on. Skills are copied as real files into your agent's skills directory (`~/.claude/skills/` for Claude Code, read natively by OpenCode).

## Skills

### Django & backend

| Skill | Description |
|-------|-------------|
| `django-expert` | Expert Django backend development — models, views, ORM, migrations, DRF |
| `django-ninja` | Django Ninja API patterns — routers, schemas, CRUD endpoints, service layer |
| `django-components` | django-components patterns — reusable template components with slots, props, composition |
| `django-pytest` | pytest-django testing — factories, fixtures, function-based tests, view-first philosophy |
| `django-simplify` | Audit Django codebases for structural problems — N+1 queries, fat views, ORM anti-patterns |
| `huey` | Huey task queue patterns — async tasks, periodic tasks, Django integration, pipelines |

### Frontend

| Skill | Description |
|-------|-------------|
| `htmx` | HTMX interaction patterns — partial rendering, Django CBV integration, OOB swaps |
| `alpinejs` | Alpine.js component patterns — directives, reactivity, Django template integration |
| `tailwind-4` | Tailwind CSS 4 patterns — theme variables, utility classes, Django template integration |

### Testing

| Skill | Description |
|-------|-------------|
| `pytest` | Pytest patterns — Factory Boy, mocker, standalone functions, Django view testing |
| `playwright` | Playwright E2E testing patterns — Page Objects, selectors, MCP workflow |

### Workflow

| Skill | Description |
|-------|-------------|
| `simplify` | Simplify and refine recently-modified code for clarity and maintainability |
| `pr-review` | Technical review of a single PR/MR — problem-first validation, root-cause checks |
| `repo-manager` | Repository/platform operations — PR/MR/issue workflows, backlog and merge coordination |
| `branch-pr` | PR creation workflow with issue-first checks |
| `linear` | Draft Linear QA comments aligned with issue requirements and commits |

## Credits

The workflow skills `branch-pr`, `pr-review`, `linear`, and `repo-manager` are derived from
[gentleman-programming/gentle-ai](https://github.com/gentleman-programming/gentle-ai) and adapted here.

## License

[MIT](./LICENSE) — except `pr-review`, which carries its own `Apache-2.0` license declared in its frontmatter.

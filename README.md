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
| `review` | PR code review workflow — problem-first validation, root-cause checks, delegates domain rules to project skills |
| `repo-manager` | Repository/platform operations — PR/MR/issue workflows, backlog and merge coordination |
| `linear` | Draft Linear QA comments aligned with issue requirements and commits |

## Credits

The workflow skills `repo-manager` are derived from
[gentleman-programming/gentle-ai](https://github.com/gentleman-programming/gentle-ai) and adapted here.

The `review` skill is authored by `grupo-ilao` and adapted here.

## License

[MIT](./LICENSE) — covers the entire collection.

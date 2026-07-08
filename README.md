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
| `simplify` | Simplify recently-modified code for clarity; escalates to deep multi-review on risk signals |
| `prepare-commit` | Pre-commit quality gate — validate changed code, architecture, and tests before staging |
| `review` | PR/diff code review workflow — independent Spec and Standards passes, root-cause checks, delegates domain rules to project skills |
| `open-pr` | Issue-first PR creation, gated on the post-implementation quality checks |
| `repo-manager` | Repository/platform operations — PR/MR/issue workflows, backlog and merge coordination |
| `create-linear-comment` | Draft Linear QA comments aligned with issue requirements and commits |

## Credits

The `repo-manager` skill is derived from
[gentleman-programming/gentle-ai](https://github.com/gentleman-programming/gentle-ai) and adapted here.

The `review`, `open-pr`, and `prepare-commit` skills are authored by `grupo-ilao` and adapted here.

## License

[MIT](./LICENSE) — covers the entire collection.

---
name: django-expert
description: Django — models, ORM, CBVs, DRF serializers/viewsets, migrations, auth, testing, performance. Trigger: any Django backend task in this project.
---

# Django Expert

## Instructions

Follow this workflow when handling Django development requests:

### 1. Analyze the Request and Gather Context

Identify the task type, then load the matching reference file from the table below. Read existing code to understand project conventions before writing anything.

### 2. Load Relevant Reference Documentation

| Task type | Reference file |
|---|---|
| Models / ORM / migrations | `references/models-and-orm.md` |
| Views / URLs / middleware | `references/views-and-urls.md` |
| DRF serializers / viewsets / pagination | `references/drf-guidelines.md` |
| Testing | `references/testing-strategies.md` |
| Security / CSRF / permissions | `references/security-checklist.md` |
| Query optimization / caching | `references/performance-optimization.md` |
| Production deployment / settings | `references/production-deployment.md` |
| Code examples | `references/examples.md` |

Read the matched reference file before writing any code.

### 3. Implement Following the Matched Reference File

The matched reference file carries the project conventions. Follow it. If the project deviates from upstream Django conventions, the reference file documents that deviation — do not override it with generic advice.

### 4. Confirm Completion

Run `python manage.py check`, verify no N+1 queries in the response path, and confirm migrations are clean.

## Bundled Resources

- `references/models-and-orm.md` — model design, relationships, custom managers, migrations
- `references/views-and-urls.md` — FBV vs CBV, mixins, URL routing, middleware, request/response lifecycle
- `references/drf-guidelines.md` — serializers, viewsets, routers, pagination, filtering, auth, versioning
- `references/testing-strategies.md` — test structure, factories, mocking, coverage, CI/CD
- `references/security-checklist.md` — CSRF/XSS/SQL injection, auth patterns, secure config, input validation
- `references/performance-optimization.md` — select_related/prefetch_related, indexing, caching, profiling, async
- `references/production-deployment.md` — DEBUG/SECRET_KEY/ALLOWED_HOSTS, HTTPS, static files, monitoring
- `references/examples.md` — practical implementation examples

## Additional Notes

**Common Pitfalls to Avoid:**
- Circular imports (use lazy references)
- Missing `related_name` on relationships
- Forgetting database indexes on frequently queried fields
- Using `get()` without exception handling
- N+1 queries in templates and serializers

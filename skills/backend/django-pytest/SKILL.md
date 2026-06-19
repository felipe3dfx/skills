---
name: django-pytest
description: Write, debug, and review pytest-django tests following project conventions: function-based tests, *_tests.py naming, Factory Boy with @register, view-first philosophy.
---

# Django Pytest Testing Skill

## Overview

This skill provides expert guidance for writing and debugging tests using pytest-django. It enforces project-specific conventions and patterns to ensure consistent, maintainable test code.

**Key Capabilities:**
- Writing view tests with authentication and permissions
- Creating Factory Boy factories with `@register` decorator
- Setting up fixtures in `conftest.py`
- Testing HTMX requests, form submissions, and email sending
- Debugging test failures and fixture issues
- Service tests for critical business logic

## Instructions

Follow this workflow when handling test-related requests:

### 1. Analyze What Needs Testing

**Identify the target:**
- View test (default approach - tests the full integration)
- Service test (only for critical/complex business logic)
- Multi-step workflow test (creation processes with multiple steps)

**Gather context:**
- Read the view/service/model code being tested
- Check existing tests in the app's `tests/` directory
- Review `conftest.py` for available fixtures (both app-level and root-level)
- Check if factories exist for the models involved

### 2. Load Relevant Reference Documentation

Based on the task, reference the appropriate bundled documentation:

- **Project conventions** -> `references/project-testing-conventions.md`
  - File naming, test structure, pytest configuration
  - Running tests, database handling, network blocking

- **Factories & fixtures** -> `references/fixtures-and-factories.md`
  - Factory Boy patterns with `@register` decorator
  - Global fixtures from root `conftest.py`
  - Composite fixture patterns

- **Test patterns** -> `references/common-test-patterns.md`
  - View tests with authentication/permissions
  - HTMX, form, email test patterns
  - Service tests and parametrize usage
  - Mocking external services

### 3. Follow Project Conventions

**Critical rules:**
- Function-based tests ONLY (no test classes)
- Test files named `*_tests.py` (NOT `test_*.py`)
- `@pytest.mark.django_db` on every test that touches the database
- Use factories via `pytest_factoryboy`, NEVER `Model.objects.create()`
- Use `django_client` fixture (not `client` or `self.client`)
- Use `authenticated_agency_user` fixture for auth context
- Mock external services at HTTP/network layer, NEVER mock internal functions
- No separator comment blocks between tests (e.g., `# ---------------------------------------------------------------------------\n# Tests for X\n# ---------------------------------------------------------------------------`). Tests are self-documenting via their function names.

**Test structure (Arrange-Act-Assert):**
```python
@pytest.mark.django_db
def test_entity_list_view(django_client, authenticated_agency_user, entity_fixture):
    # Arrange
    agency, _ = authenticated_agency_user()
    entity = entity_fixture(agency=agency)

    # Act
    response = django_client.get(
        reverse('app_name:entity_list', kwargs={'agency_slug': agency.name_slug})
    )

    # Assert
    assert response.status_code == 200
    assert entity.name in response.content.decode()
```

### 4. Validate Tests Run Correctly

Before presenting the solution:
- Verify test follows naming conventions
- Check that all required fixtures are available or created
- Ensure `@pytest.mark.django_db` is present when needed
- Confirm factories use `@register` decorator and `apps.get_model()`
- Run tests with `uv run pytest path/to/test_file.py -v` to verify

## Bundled Resources

**references/** - Project-specific testing documentation:

- **`references/project-testing-conventions.md`**
  - Test file naming and organization rules
  - pytest configuration from pyproject.toml
  - Test settings and environment
  - Running tests commands and options
  - Network blocking and database reuse

- **`references/fixtures-and-factories.md`**
  - Factory Boy with `@register` decorator pattern
  - `pytest_factoryboy` integration and auto-generated fixtures
  - Global fixtures: `django_client`, `authenticated_agency_user`, `client_agency_fixture`, `policy_fixture`, `payment_fixture`, `renewal_fixture`
  - Composite fixture patterns and factory creation examples

- **`references/common-test-patterns.md`**
  - Testing views with authentication and permissions
  - Testing HTMX requests with `HTTP_HX_REQUEST='true'`
  - Testing form submissions and email sending
  - Multi-step creation workflow tests
  - `pytest.parametrize` for test variations
  - Service tests for critical business logic
  - Mocking external services at HTTP layer

## Quick Reference

| Convention | Rule |
|---|---|
| Test files | `*_tests.py` (NOT `test_*.py`) |
| Test style | Function-based only (NO classes) |
| DB marker | `@pytest.mark.django_db` required |
| Test data | Factory Boy with `@register` (NEVER `Model.objects.create()`) |
| Client | `django_client` fixture |
| Auth | `authenticated_agency_user()` returns `(agency, user)` |
| HTMX | Pass `HTTP_HX_REQUEST='true'` as kwarg |
| Email | Use `mailoutbox` fixture |
| Mocking | Mock at HTTP layer, NEVER internal functions |
| Dates/Time | `freeze_time` from freezegun — NEVER set `created_at` manually |
| Philosophy | Test views first, services only for critical logic |

# Project Testing Conventions

## Test File Organization

### Directory Structure

```
app_name/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # App-specific fixtures
│   ├── factories.py          # Factory Boy factories
│   ├── test_utils.py         # Test utilities (if needed)
│   └── app_name_tests.py     # Main test file (e.g., customer_tests.py)
```

### File Naming Rules

- **Main test file**: `app_name_tests.py` (e.g., `customer_tests.py`, `insurance_tests.py`)
- **Service tests**: `services_tests.py` (only for critical services)
- Test files MUST end with `_tests.py` (NOT `test_*.py`)
- The `python_files` setting in `pyproject.toml` enforces this: `python_files = "tests.py *_tests.py"`

### Test Function Style

- **Function-based tests ONLY** - never use test classes (`class TestSomething`)
- Every test function that accesses the database MUST have `@pytest.mark.django_db`
- Use descriptive names: `test_entity_list_view_displays_all_entities`
- **No separator comment blocks** between tests. Never add visual dividers like:
  ```python
  # ---------------------------------------------------------------------------
  # Tests for some_service
  # ---------------------------------------------------------------------------
  ```
  Tests are grouped and understood by their descriptive function names alone.

## Pytest Configuration

From `pyproject.toml`:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.django.tests"
norecursedirs = "assets static uploads .git node_modules htmlcov .tox .cache .pnpm-store"
python_files = "tests.py *_tests.py"
addopts = "--maxfail=1 -rf -s --nomigrations --cov=. --cov-report=html --cov-report=term --numprocesses=auto --dist loadgroup --reuse-db --disable-socket --local-badge-output-dir .github/badges/"
env = ['DEBUG_TOOLBAR_ENABLED=False', 'LOGFIRE_TOKEN=']
```

### Key Configuration Details

| Setting | Value | Purpose |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.django.tests` | Test-specific Django settings |
| `--maxfail=1` | Stop after first failure | Fast feedback loop |
| `--nomigrations` | Skip migrations | Faster test startup |
| `--numprocesses=auto` | Parallel execution | Uses all CPU cores |
| `--dist loadgroup` | Load-balanced distribution | Optimal parallelism |
| `--reuse-db` | Reuse test database | Faster subsequent runs |
| `--disable-socket` | Block network calls | Prevents accidental external calls |
| `--cov` | Coverage enabled | Automatic coverage reporting |
| `-rf` | Show failed test details | Better debugging output |
| `-s` | No output capture | See print statements |

### Coverage Configuration

```toml
[tool.coverage.run]
omit = ["*/migrations/*", "*/tests/*"]
```

Migrations and test files are excluded from coverage metrics.

## Running Tests

### Common Commands

```bash
# Run all tests
uv run pytest

# Run tests for specific app
uv run pytest app_name/tests/

# Run specific test file
uv run pytest app_name/tests/app_name_tests.py

# Run specific test function
uv run pytest app_name/tests/app_name_tests.py::test_entity_list_view

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov

# Run in parallel (default)
uv run pytest -n auto

# Run tests matching a pattern
uv run pytest -k "test_insurance"

# Run with debug on first failure
uv run pytest -x --pdb

# Override maxfail to see all failures
uv run pytest --maxfail=0
```

### Important Notes

- **Network calls are blocked by default** via `pytest-socket` (`--disable-socket`). Any test making real HTTP calls will fail. Mock external services instead.
- **Database is reused** between runs (`--reuse-db`). If schema changes, delete the test database or run without `--reuse-db`.
- **Parallel execution** is on by default (`--numprocesses=auto`). Tests must be independent and not share state.
- **Test settings module**: `config.django.tests` - this may override certain Django settings for the test environment (e.g., disable debug toolbar, use in-memory cache).

## Test Naming Conventions

### Test Function Names

Use descriptive names that explain what is being tested:

```python
def test_entity_list_view_displays_all_entities():
    """Test that entity list view displays all entities for the agency."""

def test_entity_create_view_requires_authentication():
    """Test that entity create view requires user authentication."""

def test_entity_detail_view_shows_correct_information():
    """Test that entity detail view shows correct entity information."""
```

## Testing Philosophy

**Default approach: Test views, not services or models directly.**

Testing views provides the most comprehensive coverage because:
- Views integrate all components (models, services, forms, permissions)
- Tests verify the complete user workflow
- Tests catch integration issues between components
- Tests validate that the UI receives correct data

**Exception**: For complex or critical business services, create dedicated service tests focused on validation logic, not code coverage.

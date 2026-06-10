---
name: pytest
description: >
  Pytest patterns — Factory Boy, mocker, standalone functions, Django view testing.
  Trigger: When writing Python tests — fixtures, factories, mocking, Django views.
license: Apache-2.0
metadata:
  version: "2.0"
---

## When to Use

- Writing or modifying Python test files (`*_tests.py`, `test_*.py`)
- Creating factories (`factories.py`) or fixtures (`conftest.py`)
- Mocking external services or dependencies in tests
- Testing Django views, forms, permissions, or HTMX endpoints

---

## Critical Patterns

### Standalone Functions ONLY

Tests are **standalone functions** — NEVER class-based. No `TestSomething` classes, no `self` parameter.

```python
# CORRECT
@pytest.mark.django_db
def test_entity_list_view(django_client, authenticated_agency_user, entity_fixture):
    agency, _ = authenticated_agency_user()
    entity = entity_fixture(agency=agency)

    response = django_client.get(
        reverse('app_name:entity_list', kwargs={'agency_slug': agency.name_slug})
    )

    assert response.status_code == 200
    assert entity.name in response.content.decode()


# WRONG — never do this
class TestEntityViews:
    def test_entity_list_view(self):
        ...
```

### No Module-Level Docstrings

Never add a docstring at the top of any `.py` file — not in test files, not in factories, not in conftest.

```python
# WRONG
"""Tests for the customer module."""

import pytest
...

# CORRECT — start directly with imports
import pytest
...
```

### No Separator Blocks Between Tests

Never add comment separators between test functions. Tests are grouped by their descriptive names alone.

```python
# WRONG
# --- Customer List Tests ---

def test_customer_list_view():
    ...

# --- Customer Detail Tests ---

def test_customer_detail_view():
    ...

# CORRECT — just the functions, no separators
def test_customer_list_view():
    ...


def test_customer_detail_view():
    ...
```

### mocker Fixture (pytest-mock) — Not unittest.mock

Always use the `mocker` fixture from pytest-mock. Never import `unittest.mock.patch` or `MagicMock` directly.

> **Precedence note:** Project-specific testing skills (like `django-pytest`) may override
> these generic mocking patterns. When both this skill and a project-specific skill apply,
> the project-specific one takes precedence.

**Preferred: mock at the HTTP/network layer** (works for integration and view tests):

```python
# PREFERRED — mock at the HTTP boundary
@pytest.mark.django_db
def test_process_payment(django_client, authenticated_agency_user, responses):
    agency, _ = authenticated_agency_user()
    responses.add(
        responses.POST,
        'https://api.payment-provider.com/charge',
        json={'status': 'success'},
        status=200,
    )

    response = django_client.post(
        reverse('app_name:process', kwargs={'agency_slug': agency.name_slug}),
        {'amount': 100},
        follow=True,
    )

    assert response.status_code == 200
```

**Fallback: patch internal functions** (only for isolated unit tests where HTTP mocking is not applicable):

```python
# FALLBACK — internal patching for unit tests only
@pytest.mark.django_db
def test_process_payment_unit(mocker, django_client, authenticated_agency_user):
    agency, _ = authenticated_agency_user()
    mock_service = mocker.patch('apps.core.services.external_service')
    mock_service.return_value = {'status': 'success'}

    response = django_client.post(
        reverse('app_name:process', kwargs={'agency_slug': agency.name_slug}),
        {'amount': 100},
        follow=True,
    )

    assert response.status_code == 200
    mock_service.assert_called_once()
```

```python
# WRONG — never import from unittest.mock
from unittest.mock import patch, MagicMock

def test_bad_example():
    with patch('services.payment.stripe_client') as mock:
        ...
```

### Factory Boy with @register and pytest_factoryboy

Factories live in `factories.py`. Registration happens in `conftest.py` using `pytest_factoryboy.register`.

**factories.py** — Define factories:

```python
import factory
from factory.django import DjangoModelFactory

from apps.customer import models


class ClientFactory(DjangoModelFactory):
    class Meta:
        model = models.Client

    name = factory.Faker('name')
    id_number = factory.Sequence(lambda n: f'{1000000000 + n}')
    email = factory.Faker('email')
```

**conftest.py** — Register factories as fixtures:

```python
import pytest
from pytest_factoryboy import register

from apps.customer.tests import factories

register(factories.ClientFactory)
register(factories.GroupFactory)
register(factories.NaturalPersonFactory)


@pytest.fixture
def django_client() -> Client:
    return Client()


@pytest.fixture
def authenticated_agency_user(django_client, user_factory, agency_factory):
    def _authenticated_agency_user(**kwargs):
        agency = kwargs.pop('agency', agency_factory(is_active=True))
        user = user_factory(agency=agency, **kwargs)
        django_client.force_login(user)
        return agency, user

    return _authenticated_agency_user
```

After `register(factories.ClientFactory)`, pytest_factoryboy auto-creates:
- `client_factory` fixture — callable factory
- `client` fixture — single instance

### Fixture Composition Pattern

Complex fixtures return a callable (inner function) for flexible setup:

```python
@pytest.fixture
def policy_fixture(policy_factory, endorsement_factory, client_agency_fixture, agency_factory):
    def _policy_fixture(**kwargs):
        agency = kwargs.pop('agency', agency_factory())
        client = kwargs.pop('client', client_agency_fixture(agency=agency))
        policy = policy_factory(client=client, **kwargs)
        endorsement_factory(policy=policy)
        return policy

    return _policy_fixture
```

---

## Decision Tree

```
What to test?
├── View endpoint?              → Test the view (default approach)
├── Complex business service?   → Test the service directly
├── Multiple data variations?   → Use @pytest.mark.parametrize
├── Multi-step creation flow?   → Single test covering all steps
└── Reusable test data?         → Factory in factories.py + register in conftest.py

How to mock?
├── External service/API?       → HTTP-layer mock (responses/httpx_mock) preferred
│                                  mocker.patch() only as fallback for unit tests
├── Django settings?            → settings fixture (autouse if needed)
├── S3/file storage?            → mocker.patch on the storage client
└── Complex object?             → mocker.MagicMock() with attributes

Where does the fixture go?
├── Used by multiple apps?      → Root conftest.py (apps/conftest.py)
├── Used by one app only?       → App conftest.py (apps/app_name/tests/conftest.py)
└── Used by one test file?      → Same file (prefer conftest.py anyway)
```

---

## Code Examples

### View Test with Authentication

```python
@pytest.mark.django_db
def test_entity_list_view(django_client, authenticated_agency_user, entity_fixture):
    agency, _ = authenticated_agency_user()
    entity = entity_fixture(agency=agency)

    response = django_client.get(
        reverse('app_name:entity_list', kwargs={'agency_slug': agency.name_slug}),
        follow=True,
    )

    assert response.status_code == 200
    assert entity.name in response.content.decode()
```

### View Requires Authentication (Unauthenticated)

```python
@pytest.mark.django_db
def test_view_requires_authentication(django_client, agency_factory):
    agency = agency_factory()

    response = django_client.get(
        reverse('app_name:entity_list', kwargs={'agency_slug': agency.name_slug})
    )

    assert response.status_code == 302
```

### View Requires Permission

```python
@pytest.mark.django_db
def test_view_requires_permission(django_client, authenticated_agency_user):
    agency, _ = authenticated_agency_user(read_sections=[], write_sections=[])

    response = django_client.get(
        reverse('app_name:entity_list', kwargs={'agency_slug': agency.name_slug})
    )

    assert response.status_code == 403
```

### Form Submission

```python
@pytest.mark.django_db
def test_entity_create_form(django_client, authenticated_agency_user):
    agency, _ = authenticated_agency_user()

    response = django_client.post(
        reverse('app_name:entity_create', kwargs={'agency_slug': agency.name_slug}),
        {'name': 'New Entity', 'description': 'Test'},
        follow=True,
    )

    assert response.status_code == 200
    assert 'New Entity' in response.content.decode()
    from app_name.models import Entity
    assert Entity.objects.filter(name='New Entity').exists()
```

### HTMX Request

```python
@pytest.mark.django_db
def test_htmx_filter(django_client, authenticated_agency_user, entity_fixture):
    agency, _ = authenticated_agency_user()
    entity_fixture(agency=agency, name='Target Entity')

    response = django_client.get(
        reverse('app_name:entity_list', kwargs={'agency_slug': agency.name_slug}),
        {'query': 'Target'},
        HTTP_HX_REQUEST='true',
    )

    assert response.status_code == 200
    assert 'Target Entity' in response.content.decode()
```

### Parametrize for Multiple Scenarios

```python
@pytest.mark.django_db
@pytest.mark.parametrize(
    'test_case',
    [
        {
            'mock_data': {'id_number': '53067922', 'name': 'CATHERINE', 'id_type': 'cc'},
            'expected_id_field': 'id_number',
        },
        {
            'mock_data': {'id_number': '101010101', 'name': 'ANDRES', 'id_type': 'ce'},
            'expected_id_field': 'id_number',
        },
    ],
)
def test_entity_creation_with_variations(
    mocker, test_case, django_client, authenticated_agency_user
):
    agency, _ = authenticated_agency_user()
    mock_service = mocker.patch('apps.core.services.external_service')
    mock_service.return_value = test_case['mock_data']

    response = django_client.post(
        reverse('app_name:create_entity', kwargs={'agency_slug': agency.name_slug}),
        test_case['mock_data'],
        follow=True,
    )

    assert response.status_code == 200
    assert test_case['mock_data']['name'] in response.content.decode()
```

### Service Test (Critical Business Logic Only)

```python
@pytest.mark.django_db
@pytest.mark.parametrize(
    'premium, commission_rate, expected',
    [
        (1000.00, 0.10, 100.00),
        (2000.00, 0.15, 300.00),
        (0.00, 0.10, 0.00),
        (1000.00, 0.00, 0.00),
    ],
)
def test_calculate_commission(premium, commission_rate, expected):
    from app_name.services import calculate_commission

    result = calculate_commission(premium=premium, commission_rate=commission_rate)

    assert result == expected
```

### Mocking External Services

Prefer HTTP-layer mocking (`responses`, `httpx_mock`) for integration/view tests.
Fall back to `mocker.patch()` only for isolated unit tests.

```python
# PREFERRED — HTTP-layer mock
@pytest.mark.django_db
def test_external_api_call(django_client, authenticated_agency_user, responses):
    agency, _ = authenticated_agency_user()

    responses.add(
        responses.GET,
        'https://api.external-service.com/data',
        json={'id': 'abc-123', 'status': 'active'},
        status=200,
    )

    response = django_client.get(
        reverse('app_name:sync', kwargs={'agency_slug': agency.name_slug}),
        follow=True,
    )

    assert response.status_code == 200


# FALLBACK — internal patch for unit tests only
@pytest.mark.django_db
def test_external_api_call_unit(mocker, django_client, authenticated_agency_user):
    agency, _ = authenticated_agency_user()

    mock_api = mocker.patch('apps.core.services.external_api.fetch_data')
    mock_api.return_value = {'id': 'abc-123', 'status': 'active'}

    response = django_client.get(
        reverse('app_name:sync', kwargs={'agency_slug': agency.name_slug}),
        follow=True,
    )

    assert response.status_code == 200
    mock_api.assert_called_once()
```

### Multi-Step Workflow (Exception to One-Test-Per-View)

```python
@pytest.mark.django_db
def test_complete_creation_workflow(django_client, authenticated_agency_user, mocker):
    agency, _ = authenticated_agency_user()

    # Step 1: Upload
    step_1 = django_client.post(
        reverse('app_name:upload', kwargs={'agency_slug': agency.name_slug}),
        {'file': get_test_pdf()},
        follow=True,
    )
    assert step_1.status_code == 200

    # Step 2: Process
    step_2 = django_client.get(
        reverse('app_name:process', kwargs={'agency_slug': agency.name_slug}),
        follow=True,
    )
    assert step_2.status_code == 200

    # Step 3: Confirm
    step_3 = django_client.post(
        reverse('app_name:confirm', kwargs={'agency_slug': agency.name_slug}),
        {'name': 'Final Entity'},
        follow=True,
    )
    assert step_3.status_code == 200
    assert 'Final Entity' in step_3.content.decode()
```

### Email Assertion

```python
@pytest.mark.django_db
def test_export_sends_email(django_client, authenticated_agency_user, entity_fixture, mailoutbox):
    agency, _ = authenticated_agency_user()
    entity_fixture(agency=agency)

    response = django_client.get(
        reverse('app_name:list_export', kwargs={'agency_slug': agency.name_slug})
    )

    assert response.status_code == 200
    assert len(mailoutbox) == 1
    assert 'Lista de entidades' in mailoutbox[0].subject
```

---

## Test File Structure

```
app_name/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # App-specific fixtures + factory registration
│   ├── factories.py          # Factory Boy factories (DjangoModelFactory)
│   ├── test_utils.py         # Test utilities (optional)
│   └── app_name_tests.py     # Main test file (view tests)
```

- Main test file: `app_name_tests.py` (e.g., `customer_tests.py`)
- Service tests (only for critical logic): `services_tests.py`
- One test function per view (exception: multi-step workflows)

---

## Commands

```bash
uv run pytest                                           # Run all tests
uv run pytest app_name/tests/                           # Run tests for specific app
uv run pytest app_name/tests/app_name_tests.py          # Run specific test file
uv run pytest app_name/tests/app_name_tests.py::test_entity_list_view  # Run single test
uv run pytest -v                                        # Verbose output
uv run pytest -x                                        # Stop on first failure
uv run pytest -k "test_customer"                        # Filter by name
uv run pytest --cov                                     # With coverage
uv run pytest -n auto                                   # Parallel (pytest-xdist)
uv run pytest --tb=short                                # Short traceback
```

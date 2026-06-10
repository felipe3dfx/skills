# Fixtures and Factories

## Factory Boy Pattern

All factories follow this pattern:

1. Use `@register` decorator from `pytest_factoryboy`
2. Extend `factory.django.DjangoModelFactory`
3. Use `apps.get_model()` in `Meta.model` (not direct model import)
4. Use `factory.LazyAttribute` for generated values
5. Use `factory.SubFactory` for related models (string path to avoid circular imports)

### Factory Example

```python
import factory
from django.apps import apps
from faker import Factory as FakerFactory
from pytest_factoryboy import register

faker = FakerFactory.create()


@register
class AgencyFactory(factory.django.DjangoModelFactory):
    """Factory for agency model."""

    name = factory.LazyAttribute(lambda x: faker.company())
    phone = factory.LazyAttribute(lambda x: faker.phone_number())
    short_name = factory.LazyAttribute(lambda x: faker.slug())

    class Meta:
        model = apps.get_model('business', 'Agency')


@register
class SellerFactory(factory.django.DjangoModelFactory):
    """Factory for seller model."""

    agency = factory.SubFactory('apps.business.tests.factories.AgencyFactory')
    name = factory.LazyAttribute(lambda x: faker.name())
    id_number = factory.LazyAttribute(lambda x: faker.random_number(8, True))

    class Meta:
        model = apps.get_model('business', 'Seller')
```

### Key Patterns

| Pattern | Usage | Example |
|---|---|---|
| `factory.LazyAttribute` | Generated values | `lambda x: faker.company()` |
| `factory.SubFactory` | FK relationships | `factory.SubFactory('path.to.Factory')` |
| `factory.Faker` | Direct faker integration | `factory.Faker('email')` |
| `@register` | Auto-registers as pytest fixture | Generates `agency_factory` fixture |

### How `@register` Works

The `@register` decorator from `pytest_factoryboy` automatically creates two fixtures:
- `agency_factory` - A callable fixture that creates instances (use this in tests)
- `agency` - A single pre-created instance (less commonly used)

Factories are registered in the root `apps/conftest.py` file, making them globally available.

### Using Enum Values in Factory Parameters

When passing choices/enum fields to factory fixtures, always use the model's enum class — not plain strings:

```python
# CORRECT — enum value is explicit and type-safe
sale_factory(sales_mode=Sale.SalesMode.TMK)

# WRONG — plain string is fragile and loses type safety
sale_factory(sales_mode='TMK')
```

Import the model at the top of the test file for enum access:

```python
from apps.sales.models import Sale
```

## Factory Registration (Root conftest.py)

All factories are imported and registered in `apps/conftest.py`:

```python
from pytest_factoryboy import register

from apps.business.tests import factories as business_factories
from apps.customer.tests import factories as customer_factories
from apps.insurance.tests import factories as insurance_factories
# ... more imports

register(business_factories.AgencyFactory)
register(business_factories.InsurerCompanyFactory)
register(customer_factories.ClientFactory)
register(insurance_factories.PolicyFactory)
# ... more registrations
```

This double registration (once in factories.py with `@register` decorator, once in conftest.py) ensures all factories are available as fixtures in all test files.

### Available Factory Fixtures

From the root `apps/conftest.py`, these factory fixtures are globally available:

**Core:**
- `economic_activity_factory`, `country_factory`, `department_factory`, `city_factory`

**Business:**
- `category_factory`, `sub_ramo_factory`, `ramo_factory`, `agency_factory`
- `insurer_company_factory`, `seller_factory`, `seller_commission_factory`, `default_commission_factory`

**Customer:**
- `group_factory`, `client_factory`, `natural_person_factory`, `legal_person_factory`
- `legal_person_contact_factory`, `consortium_factory`, `client_document_factory`, `client_agency_factory`

**Insurance:**
- `policy_factory`, `endorsement_factory`, `agency_share_factory`
- `seller_share_factory`, `policy_document_factory`

**Operation:**
- `payment_factory`, `payment_amount_factory`, `settlement_factory`
- `task_type_factory`, `task_factory`

**User:**
- `user_factory`

**Notification:**
- `external_notification_factory`, `attachment_factory`

**Renewal:**
- `renewal_status_factory`, `renewal_sub_status_factory`, `renewal_factory`

**API:**
- `key_factory`, `policy_file_factory`, `payment_file_factory`
- `customer_file_factory`, `sarlaft_file_factory`

## Global Fixtures

### `django_client`

Simple Django test client instance:

```python
@pytest.fixture
def django_client() -> Client:
    return Client()
```

Use this for all HTTP requests in tests. Do NOT use the built-in `client` fixture.

### `authenticated_agency_user`

The most important fixture. Creates an authenticated user with agency access and permissions:

```python
@pytest.fixture
def authenticated_agency_user(django_client, user_factory, agency_factory):
    def _authenticated_agency_user(**kwargs):
        agency = kwargs.pop('agency', agency_factory())
        all_sections = [x[0] for x in SECTION_CHOICES]
        read_sections = kwargs.pop('read_sections', all_sections)
        write_sections = kwargs.pop('write_sections', all_sections)
        export_sections = kwargs.pop('export_sections', all_sections)
        user = user_factory(
            agency=agency,
            read_sections=read_sections,
            write_sections=write_sections,
            export_sections=export_sections,
            **kwargs,
        )
        django_client.force_login(user)
        return agency, user

    return _authenticated_agency_user
```

**Usage:**

```python
# Default: full permissions on all sections
agency, user = authenticated_agency_user()

# Custom permissions:
agency, user = authenticated_agency_user(
    read_sections=['insurance', 'customer'],
    write_sections=['insurance'],
    export_sections=[],
)

# With specific agency:
agency, user = authenticated_agency_user(agency=my_agency)

# No permissions (for testing 403 responses):
agency, user = authenticated_agency_user(
    read_sections=[],
    write_sections=[],
)
```

**Returns:** `(agency, user)` tuple. The user is already logged in via `django_client.force_login()`.

### `client_agency_fixture`

Creates a complete client (customer) with the appropriate person type:

```python
# Creates a natural person client linked to an agency
client = client_agency_fixture(agency=agency)

# With custom natural person data
client = client_agency_fixture(
    agency=agency,
    natural_person_kwargs={'first_name': 'John'},
)
```

Automatically creates the associated NaturalPerson, LegalPerson, or Consortium based on the client type.

### `policy_fixture`

Creates a complete policy with all related objects (endorsement, term, agency share):

```python
policy = policy_fixture(agency=agency)

# With specific client
policy = policy_fixture(agency=agency, client=my_client)

# With custom policy data
policy = policy_fixture(
    agency=agency,
    policy_kwargs={'number': 'POL-001'},
)
```

This fixture:
1. Creates a client (if not provided)
2. Creates an agency (if not provided)
3. Links client to agency via `ClientAgency`
4. Creates a policy with an initial endorsement
5. Runs `RelateEndorsementTerm` service to create terms
6. Updates computed data on endorsements, terms, and policy

### `payment_fixture`

Creates a payment with associated policy and payment amounts:

```python
payment = payment_fixture(agency=agency)

# With specific policy
payment = payment_fixture(agency=agency, policy=my_policy)
```

### `renewal_fixture`

Creates a renewal with all required status objects:

```python
renewal = renewal_fixture()

# With specific policy
renewal = renewal_fixture(policy=my_policy)
```

Creates initial status, closed status (with success/failed sub-statuses), and links to a policy.

## Creating New Factories

When adding a new factory:

1. Create in `apps/{app_name}/tests/factories.py`
2. Use the `@register` decorator
3. Use `apps.get_model('app_name', 'ModelName')` for the Meta model
4. Add registration in `apps/conftest.py`
5. Use `factory.SubFactory` with string paths for FK fields

```python
# apps/my_app/tests/factories.py
import factory
from django.apps import apps
from faker import Factory as FakerFactory
from pytest_factoryboy import register

faker = FakerFactory.create()


@register
class MyModelFactory(factory.django.DjangoModelFactory):
    """Factory for MyModel."""

    name = factory.LazyAttribute(lambda x: faker.text(max_nb_chars=50))
    agency = factory.SubFactory('apps.business.tests.factories.AgencyFactory')

    class Meta:
        model = apps.get_model('my_app', 'MyModel')
```

Then in `apps/conftest.py`:
```python
from apps.my_app.tests import factories as my_app_factories
register(my_app_factories.MyModelFactory)
```

## Creating New Composite Fixtures

For complex test scenarios, create composite fixtures in `conftest.py`:

```python
@pytest.fixture
def my_scenario_fixture(my_model_factory, policy_fixture, agency_factory):
    def _my_scenario_fixture(**kwargs):
        agency = kwargs.pop('agency', agency_factory())
        policy = policy_fixture(agency=agency)
        my_model = my_model_factory(agency=agency, policy=policy, **kwargs)
        return my_model

    return _my_scenario_fixture
```

Key patterns:
- Use the inner function pattern (`def _fixture(**kwargs)`) for flexibility
- Accept `**kwargs` and pop known params with defaults
- Return the main object being tested
- Compose simpler fixtures rather than duplicating setup logic

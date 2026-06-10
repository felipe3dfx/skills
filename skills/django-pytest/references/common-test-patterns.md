# Common Test Patterns

## Testing Views with Authentication

Most views require an authenticated user. Use the `authenticated_agency_user` fixture:

```python
@pytest.mark.django_db
def test_entity_list_view(django_client, authenticated_agency_user, entity_fixture):
    """Test entity list view displays all entities."""
    agency, _ = authenticated_agency_user()
    entity = entity_fixture(agency=agency)

    response = django_client.get(
        reverse('app_name:entity_list', kwargs={'agency_slug': agency.name_slug})
    )

    assert response.status_code == 200
    assert entity.name in response.content.decode()
```

### Testing Unauthenticated Access

```python
@pytest.mark.django_db
def test_view_requires_authentication(django_client, agency_factory):
    """Test that view requires authentication."""
    agency = agency_factory()

    response = django_client.get(
        reverse('app_name:entity_list', kwargs={'agency_slug': agency.name_slug})
    )

    # Should redirect to login
    assert response.status_code == 302
```

## Testing Views with Permissions

Control permissions via `authenticated_agency_user` kwargs:

```python
@pytest.mark.django_db
def test_view_requires_permission(django_client, authenticated_agency_user):
    """Test that view requires specific permission."""
    agency, user = authenticated_agency_user(
        read_sections=[],   # No read permissions
        write_sections=[],  # No write permissions
    )

    response = django_client.get(
        reverse('app_name:entity_list', kwargs={'agency_slug': agency.name_slug})
    )

    assert response.status_code == 403  # Forbidden
```

### Testing Read-Only Access

```python
@pytest.mark.django_db
def test_user_with_read_only_cannot_create(django_client, authenticated_agency_user):
    """Test that user with read-only access cannot create entities."""
    agency, _ = authenticated_agency_user(
        read_sections=['insurance'],
        write_sections=[],  # No write access
    )

    response = django_client.post(
        reverse('app_name:entity_create', kwargs={'agency_slug': agency.name_slug}),
        {'name': 'New Entity'},
    )

    assert response.status_code == 403
```

## Testing HTMX Requests

HTMX requests are identified by the `HX-Request` header. Pass it via `HTTP_HX_REQUEST`:

```python
@pytest.mark.django_db
def test_htmx_filter_request(django_client, authenticated_agency_user, entity_fixture):
    """Test HTMX filter request returns partial template."""
    agency, _ = authenticated_agency_user()
    entity_fixture(agency=agency, name='Test Entity')

    response = django_client.get(
        reverse('app_name:entity_list', kwargs={'agency_slug': agency.name_slug}),
        {'query': 'Test'},
        HTTP_HX_REQUEST='true',
    )

    assert response.status_code == 200
    assert 'Test Entity' in response.content.decode()
```

### HTMX POST Requests

```python
@pytest.mark.django_db
def test_htmx_delete_request(django_client, authenticated_agency_user, entity_fixture):
    """Test HTMX delete request."""
    agency, _ = authenticated_agency_user()
    entity = entity_fixture(agency=agency)

    response = django_client.post(
        reverse('app_name:entity_delete', kwargs={
            'agency_slug': agency.name_slug,
            'pk': entity.pk,
        }),
        HTTP_HX_REQUEST='true',
    )

    assert response.status_code == 200
```

## Testing Form Submissions

```python
@pytest.mark.django_db
def test_entity_create_form_submission(django_client, authenticated_agency_user):
    """Test entity creation form submission."""
    agency, _ = authenticated_agency_user()

    response = django_client.post(
        reverse('app_name:entity_create', kwargs={'agency_slug': agency.name_slug}),
        {
            'name': 'New Entity',
            'description': 'Test description',
        },
        follow=True,
    )

    assert response.status_code == 200
    assert 'New Entity' in response.content.decode()

    # Verify entity was created in database
    from app_name.models import Entity
    assert Entity.objects.filter(name='New Entity').exists()
```

### Testing Invalid Form Data

```python
@pytest.mark.django_db
def test_entity_create_with_invalid_data(django_client, authenticated_agency_user):
    """Test that invalid form data shows errors."""
    agency, _ = authenticated_agency_user()

    response = django_client.post(
        reverse('app_name:entity_create', kwargs={'agency_slug': agency.name_slug}),
        {'name': ''},  # Required field empty
    )

    assert response.status_code == 200  # Re-renders form
    assert 'error' in response.content.decode().lower()
```

## Testing Email Sending

Use the `mailoutbox` fixture from `pytest-django`:

```python
@pytest.mark.django_db
def test_export_sends_email(django_client, authenticated_agency_user, entity_fixture, mailoutbox):
    """Test that export view sends email with report."""
    agency, _ = authenticated_agency_user()
    entity_fixture(agency=agency)

    response = django_client.get(
        reverse('app_name:list_export', kwargs={'agency_slug': agency.name_slug})
    )

    assert response.status_code == 200
    assert len(mailoutbox) == 1
    assert 'Lista de entidades' in mailoutbox[0].subject
```

### Verifying Email Content

```python
assert len(mailoutbox) == 1
email = mailoutbox[0]
assert email.subject == 'Expected Subject'
assert 'expected content' in email.body
assert email.to == ['recipient@example.com']
assert len(email.attachments) == 1  # If attachment expected
```

## Multi-Step Creation Workflows

For creation processes with multiple steps, test the entire workflow in a single test:

```python
@pytest.mark.django_db
def test_entity_creation_process(django_client, authenticated_agency_user, mocker):
    """Test complete entity creation workflow."""
    agency, _ = authenticated_agency_user()

    # Step 1: Upload document
    step_1 = django_client.post(
        reverse('app_name:upload_document', kwargs={'agency_slug': agency.name_slug}),
        {'file': get_test_pdf()},
        follow=True,
    )
    assert step_1.status_code == 200

    # Step 2: Process document
    step_2 = django_client.get(
        reverse('app_name:process_document', kwargs={'agency_slug': agency.name_slug}),
        follow=True,
    )
    assert step_2.status_code == 200

    # Step 3: Create entity
    step_3 = django_client.post(
        reverse('app_name:create_entity', kwargs={'agency_slug': agency.name_slug}),
        {'name': 'Test Entity'},
        follow=True,
    )
    assert step_3.status_code == 200
    assert 'Test Entity' in step_3.content.decode()
```

## Using pytest.parametrize

Test multiple scenarios with the same test logic:

```python
@pytest.mark.django_db
@pytest.mark.parametrize(
    'test_case',
    [
        {
            'mock_data': {
                'id_number': '53067922',
                'name': 'CATHERINE',
                'surname': 'WIESNER ANGULO',
                'id_type': 'cc',
            },
            'expected_id_field': 'id_number',
        },
        {
            'mock_data': {
                'id_number': '101010101',
                'name': 'ANDRES',
                'surname': 'PEREZ LOPEZ',
                'id_type': 'ce',
            },
            'expected_id_field': 'id_number',
        },
    ],
)
def test_entity_creation_with_variations(
    mocker, test_case, django_client, authenticated_agency_user
):
    """Test entity creation with different data variations."""
    agency, _ = authenticated_agency_user()
    # ... test logic using test_case data
```

### Parametrize for Service Tests

```python
@pytest.mark.django_db
@pytest.mark.parametrize(
    'premium, commission_rate, expected_commission',
    [
        (1000.00, 0.10, 100.00),   # 10% commission
        (2000.00, 0.15, 300.00),   # 15% commission
        (500.00, 0.05, 25.00),     # 5% commission
        (0.00, 0.10, 0.00),        # Zero premium
        (1000.00, 0.00, 0.00),     # Zero commission rate
    ],
)
def test_calculate_commission(premium, commission_rate, expected_commission):
    """Test commission calculation with various parameters."""
    from app_name.services import calculate_commission

    result = calculate_commission(premium=premium, commission_rate=commission_rate)

    assert result == expected_commission
```

## Service Tests for Critical Business Logic

Only create service tests for complex/critical operations. Focus on validations and calculations, NOT code coverage.

```python
@pytest.mark.django_db
@pytest.mark.parametrize(
    'policy_status, payment_status, expected_result',
    [
        ('active', 'paid', True),
        ('active', 'pending', False),
        ('cancelled', 'paid', False),
        ('expired', 'paid', False),
    ],
)
def test_can_renew_policy(policy_status, payment_status, expected_result):
    """Test policy renewal eligibility with different status combinations."""
    from app_name.services import can_renew_policy

    policy = policy_factory(status=policy_status)
    payment = payment_factory(policy=policy, status=payment_status)

    result = can_renew_policy(policy=policy)

    assert result == expected_result
```

## Mocking External Services

**Critical rule**: Mock at HTTP/network layer, NEVER mock internal project functions.

```python
@pytest.mark.django_db
def test_external_api_call(mocker, django_client, authenticated_agency_user):
    """Test view that calls external API."""
    agency, _ = authenticated_agency_user()

    # CORRECT: Mock at HTTP layer
    mock_response = mocker.Mock()
    mock_response.json.return_value = {'status': 'success'}
    mock_response.status_code = 200
    mocker.patch('requests.Session.request', return_value=mock_response)

    response = django_client.get(
        reverse('app_name:external_data', kwargs={'agency_slug': agency.name_slug})
    )

    assert response.status_code == 200
```

### What NOT to Do

```python
# WRONG: Don't mock internal functions
mocker.patch('apps.business.services.business_create')  # BAD

# WRONG: Don't mock at high-level service layer
mocker.patch('apps.insurance.services.policy.create_policy')  # BAD

# CORRECT: Mock at the boundary (HTTP requests, external APIs)
mocker.patch('requests.Session.request', return_value=mock_response)  # GOOD
mocker.patch('google.generativeai.GenerativeModel.generate_content')  # GOOD (external API)
```

## Testing with Deterministic Dates (freezegun)

Any test that depends on dates or time MUST use `freezegun` to control time. **Never set `created_at` or date fields manually** — freeze time and let Django/factories assign timestamps naturally.

**Decorator** — entire test runs at a fixed point in time:

```python
from freezegun import freeze_time

@freeze_time('2024-12-23 12:00:00')
@pytest.mark.django_db
def test_invoice_due_within_30_days(invoice_factory):
    """Invoices created today are due within the 30-day window."""
    invoice = invoice_factory()  # created_at = 2024-12-23 12:00:00
    assert invoice.is_due_soon is True
```

**Context manager** — create records at different points in time:

```python
@freeze_time('2024-06-15 12:00:00')
@pytest.mark.django_db
def test_certificate_editable_within_90_days(user_factory, certificate_factory):
    """Non-staff can edit certificates within 90 days of creation."""
    user = user_factory(is_staff=False, can_approve_certificate=True)

    # Certificate created 30 days ago
    with freeze_time('2024-05-15 12:00:00'):
        certificate = certificate_factory(status='approved')

    # "Now" is June 15 — within 90-day window
    assert can_edit_certificate(user=user, certificate=certificate) is True
```

**With timezone offset** — when business logic depends on local time:

```python
@freeze_time('2024-12-23 12:00:00', tz_offset=+5)
@pytest.mark.django_db
def test_premium_calculation_with_timezone(certificate_factory):
    certificate = certificate_factory(premium=500.0)
    # timezone.now() returns 2024-12-23 17:00:00+05:00
```

**Rules:**
- NEVER set `created_at=datetime(...)` manually — freeze time instead
- ALWAYS use `freeze_time` for expiration, aging, or date-windowed logic
- Combine decorator (outer "now") + context manager (inner "past") for multi-date scenarios
- Use `tz_offset` when business logic depends on local time, not UTC

## Test Utilities

Project-wide test utilities live in `app/test_utils.py`:

```python
from app.test_utils import get_test_pdf, get_test_image
```

Use these for file upload tests instead of creating test files inline.

## Best Practices Summary

1. **Use fixtures**: Always use fixtures from `conftest.py` instead of creating data inline
2. **Test views first**: Default to testing views for comprehensive coverage
3. **One test per view**: Each view should have its own test function
4. **Use parametrize**: Test variations with `@pytest.mark.parametrize`
5. **Test complete workflows**: For multi-step processes, test the entire workflow
6. **Service tests for critical logic**: Only create service tests for complex/critical business logic
7. **Focus on validations**: In service tests, focus on calculations and business rules
8. **Descriptive names**: Use clear, descriptive test function names
9. **Assert meaningful things**: Assert business logic, not implementation details
10. **Use factories**: Always use Factory Boy factories for test data

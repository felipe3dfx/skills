---
name: django-ninja
description: >
  Django Ninja API patterns — Routers, Schemas, CRUD endpoints, service layer integration.
  Trigger: When building REST APIs with Django Ninja — routers, schemas, endpoints.
license: Apache-2.0
metadata:
  version: "1.0"
---

## When to Use

- Creating or modifying REST API endpoints with Django Ninja
- Defining request/response schemas (Pydantic, NOT DRF serializers)
- Wiring API endpoints to the service layer
- Adding authentication, error handling, filtering, or pagination to API routes

---

## Critical Patterns

### Pattern 1: NEVER Use DRF Concepts

Django Ninja is NOT Django REST Framework. Never use `Serializer`, `ModelSerializer`, `ViewSet`, `APIView`, or `permission_classes`.

| DRF (WRONG)                | Django Ninja (CORRECT)             |
|----------------------------|------------------------------------|
| `Serializer`               | `Schema` / `ModelSchema`           |
| `ViewSet` + `@action`      | `@router.get()`, `@router.post()`  |
| `router.register()`        | `api.add_router()`                 |
| `permission_classes`        | `auth=` parameter                  |
| `serializer.validated_data` | Pydantic model instance            |
| `serializer.data`           | `response=` schema                 |

### Pattern 2: Thin Endpoints, Fat Services

Endpoint functions are orchestration only. ALL business logic lives in `services.py`.

```python
# api.py
@router.post('/', response={201: EntityOutSchema})
def create_entity(request: HttpRequest, payload: EntityInSchema) -> Entity:
    return entity_services.entity_create_service(payload=payload.dict())
```

```python
# services.py
def entity_create_service(*, payload: dict) -> Entity:
    with transaction.atomic():
        entity = Entity.objects.create(**payload)
        return entity
```

### Pattern 3: No Module-Level Docstrings

Never add a module-level docstring at the top of any `.py` file. Start directly with imports.

```python
# WRONG
"""API endpoints for sales."""
from ninja import Router
...

# CORRECT
from ninja import Router
...
```

### Pattern 4: Code in English, User-Facing in Spanish

- Variable names, function names, class names, comments, docstrings: **English**
- Error messages shown to users, validation messages, verbose names: **Spanish**

```python
@field_validator('contract_number')
@classmethod
def validate_contract_number(cls, contract_number: str) -> str:
    if len(contract_number) < 3:
        raise ValueError('El numero de contrato debe tener minimo 3 digitos')
    return contract_number
```

---

## Decision Tree

```
New API endpoint?           -> Create in app's api.py with Router
Need data validation?       -> Ninja Schema (not DRF Serializer)
Schema from model?          -> ModelSchema with explicit fields tuple
Complex business logic?     -> Delegate to services.py
Need filtering?             -> FilterSchema + Query(...)
Need pagination?            -> @paginate(PageNumberPagination)
Custom pagination?          -> Extend PageNumberPagination (see ExtendedPageNumberPagination)
File upload (base64)?       -> Schema with base64_file field + decode in endpoint
Need auth on all routes?    -> Router(auth=GlobalAuth()) or router-level auth
Need auth on one route?     -> @router.get('/path', auth=BearerAuth())
Skip auth on one route?     -> @router.post('/path', auth=None)
Multiple status codes?      -> response={201: OutSchema, 400: ErrorSchema}
```

---

## Code Examples

### Example 1: NinjaAPI Setup with Global Auth and Routers

```python
# urls.py
from django.core.exceptions import RequestDataTooBig
from django.http import HttpRequest, JsonResponse
from ninja import NinjaAPI
from ninja.security import HttpBasicAuth

from apps.api.api import router
from apps.sales.api import router as sales_router


class GlobalAuth(HttpBasicAuth):
    def authenticate(self, request: HttpRequest, username: str, password: str) -> Key | None:
        try:
            key = Key.objects.get(public_key=username)
            # validate token...
            return key
        except Key.DoesNotExist:
            return None


api = NinjaAPI(
    title='My API',
    version='1.0.0',
    auth=GlobalAuth(),
    urls_namespace='api',
    docs_url='/docs',
    openapi_url='/openapi.json',
)


@api.exception_handler(RequestDataTooBig)
def handle_request_data_too_big(request: HttpRequest, exc: RequestDataTooBig) -> JsonResponse:
    return JsonResponse({'message': 'File is too large.'}, status=413)


api.add_router('', router)
api.add_router('sales', sales_router)
```

### Example 2: Router with CRUD Endpoints

```python
# app_name/api.py
from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import paginate, PageNumberPagination

from apps.app_name import schemas
from apps.app_name.models import Entity
from apps.app_name.services import entity as entity_services

router = Router()


@router.get(
    '/',
    tags=['entities'],
    summary='List all entities',
    response={200: list[schemas.EntityListSchema]},
)
@paginate(PageNumberPagination)
def list_entities(request: HttpRequest) -> QuerySet[Entity]:  # noqa: ARG001
    return Entity.objects.select_related('related_model').all()


@router.get(
    '/{id_slug}',
    tags=['entities'],
    summary='Get entity by ID',
    response={200: schemas.EntityOutSchema, 404: dict},
)
def get_entity(request: HttpRequest, id_slug: str) -> Entity:  # noqa: ARG001
    return get_object_or_404(Entity, id_slug=id_slug)


@router.post(
    '/',
    tags=['entities'],
    summary='Create an entity',
    response={201: schemas.EntityOutSchema},
)
def create_entity(request: HttpRequest, payload: schemas.EntityInSchema) -> Entity:  # noqa: ARG001
    return entity_services.entity_create_service(payload=payload.dict())


@router.put(
    '/{id_slug}',
    tags=['entities'],
    summary='Update an entity',
    response={200: schemas.EntityOutSchema, 404: dict},
)
def update_entity(
    request: HttpRequest,  # noqa: ARG001
    id_slug: str,
    payload: schemas.EntityInSchema,
) -> Entity:
    entity = get_object_or_404(Entity, id_slug=id_slug)
    return entity_services.entity_update_service(entity=entity, payload=payload.dict())


@router.patch(
    '/{id_slug}',
    tags=['entities'],
    summary='Partial update an entity',
    response={200: schemas.EntityOutSchema, 404: dict},
)
def patch_entity(
    request: HttpRequest,  # noqa: ARG001
    id_slug: str,
    payload: schemas.EntityPatchSchema,
) -> Entity:
    entity = get_object_or_404(Entity, id_slug=id_slug)
    return entity_services.entity_update_service(
        entity=entity,
        payload=payload.model_dump(exclude_unset=True),
    )
```

### Example 3: Schema Definitions (Schema, ModelSchema, FilterSchema)

```python
# app_name/schemas.py
from ninja import FilterSchema, ModelSchema, Schema
from pydantic import BaseModel, Field, field_validator, model_validator

from apps.app_name.models import Entity


# Plain Schema — for non-model payloads
class TokenSchema(Schema):
    token: str = Field(description='JWT token')


# ModelSchema — auto-generates fields from model, always use explicit fields tuple
class EntityOutSchema(ModelSchema):
    related_name: str | None

    @staticmethod
    def resolve_related_name(obj: Entity) -> str | None:
        return obj.related.name if obj.related else None

    class Meta:
        model = Entity
        fields = ('id_slug', 'name', 'created_at')


class EntityInSchema(ModelSchema):
    class Meta:
        model = Entity
        fields = ('name', 'vendu_id')


class EntityListSchema(ModelSchema):
    class Meta:
        model = Entity
        fields = ('id_slug', 'name')


# Patch Schema — all fields optional via BaseModel
class EntityPatchSchema(BaseModel):
    name: str | None = None
    status: str | None = None

    @model_validator(mode='after')
    def validate_at_least_one(self) -> EntityPatchSchema:
        if not any(self.model_dump(exclude_unset=True).values()):
            raise ValueError('Debe proporcionar al menos un campo para actualizar.')
        return self


# FilterSchema — auto-applies non-None fields to queryset
class EntityFilterSchema(FilterSchema):
    is_active: bool | None = None
    date_from: datetime.date | None = None
    date_to: datetime.date | None = None

    def filter_date_from(self, value: datetime.date) -> Q:
        return Q(created_at__date__gte=value)

    def filter_date_to(self, value: datetime.date) -> Q:
        return Q(created_at__date__lte=value)
```

### Example 4: Error Handling

```python
from django.core.exceptions import ValidationError
from ninja.errors import HttpError

# In endpoints — use HttpError for HTTP-level errors
@router.get('/{file_id}')
def get_file(request: HttpRequest, file_id: str) -> dict:
    try:
        obj = MyModel.objects.get(id_slug=file_id)
    except MyModel.DoesNotExist as exc:
        raise HttpError(404, 'File not found') from exc
    return {'report': obj.report}

# In NinjaAPI setup — global exception handlers
@api.exception_handler(ValidationError)
def validation_error_handler(request: HttpRequest, exc: ValidationError) -> JsonResponse:
    return api.create_response(request, {'detail': exc.message_dict}, status=400)

# In services — raise Django ValidationError or custom BusinessError
from apps.core.exceptions import BusinessError

def my_service(*, data: dict) -> Model:
    if invalid_condition:
        raise BusinessError('Datos invalidos')
    ...
```

### Example 5: File Upload (Base64)

```python
# schemas.py
class FileUploadSchema(Schema):
    base64_file: str = Field(
        description='Base64 encoded file content. Supports PDF, PNG, JPG, JPEG.',
    )

# api.py
import base64
import binascii
import mimetypes

import magic
from django.core.files.base import ContentFile
from ninja.errors import HttpError


@router.post('/analyze', response={200: dict, 400: dict})
def analyze_file(request: HttpRequest, data: FileUploadSchema) -> dict:  # noqa: ARG001
    try:
        file_content = base64.b64decode(data.base64_file)
        mime_type = magic.Magic(mime=True).from_buffer(file_content)
        extension = mimetypes.guess_extension(mime_type)

        if extension not in ('.pdf', '.png', '.jpg', '.jpeg'):
            raise HttpError(400, 'Invalid file type')

        file_instance = MyFileModel(
            file=ContentFile(file_content, name=f'uploaded{extension}'),
        )
        file_instance.save()
        tasks.process_file(file_id_slug=file_instance.id_slug)
    except binascii.Error as exc:
        raise HttpError(400, 'Invalid base64 encoding') from exc
    return {'file_id': file_instance.id_slug}
```

### Example 6: Custom Pagination

```python
import math
from typing import Any

from ninja import Schema
from ninja.pagination import PageNumberPagination


class ExtendedPageNumberPagination(PageNumberPagination):
    class Output(Schema):
        items: list[Any]
        count: int
        total_pages: int
        current_page: int

    def paginate_queryset(self, queryset, pagination, request, **params):
        result = super().paginate_queryset(queryset, pagination, request, **params)
        count = result['count']
        page_size = self._get_page_size(pagination.page_size)
        result['total_pages'] = math.ceil(count / page_size) if count > 0 else 0
        result['current_page'] = pagination.page
        return result
```

### Example 7: Filtering with FilterSchema

```python
# api.py
from ninja import Query

@router.get('/', response={200: list[schemas.SaleOutSchema]})
@paginate(ExtendedPageNumberPagination)
def list_sales(
    request: HttpRequest,  # noqa: ARG001
    filters: Query[schemas.SaleListFilterSchema],
) -> QuerySet[Sale]:
    return filters.filter(Sale.objects.prefetch_related('related_set'))
```

### Example 8: Multiple Response Status Codes

```python
from apps.core.exceptions import BusinessError

@router.post('/import', response={200: dict, 400: dict})
def import_data(request: HttpRequest, payload: ImportSchema) -> dict:  # noqa: ARG001
    try:
        return my_services.import_request(
            base64_file=payload.base64_file,
            email=payload.email,
        )
    except BusinessError as exc:
        raise HttpError(400, str(exc)) from exc
```

---

## Commands

```bash
# Run API tests
pytest apps/api/tests/ -v

# Run specific test file
pytest apps/sales/tests/api_tests.py -v

# Check OpenAPI docs (dev server)
# Visit http://localhost:8000/api/v1/docs

# Lint API code
ruff check apps/api/ apps/sales/api.py apps/core/api.py
```

---

## Resources

- **Reference docs**: See `.agents/skills/django-expert/references/django-ninja-guidelines.md` in the project
- **Django Ninja docs**: https://django-ninja.dev

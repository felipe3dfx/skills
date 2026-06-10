---
name: huey
description: >
  Huey task queue patterns — async tasks, periodic tasks, Django integration, pipelines.
  Trigger: When creating async tasks with Huey — @db_task, @db_periodic_task, task pipelines.
license: Apache-2.0
metadata:
  version: "1.0"
---

## When to Use

- Creating async background tasks with `@db_task()`
- Creating scheduled/recurring tasks with `@db_periodic_task()`
- Configuring Huey with Redis backend in Django
- Building task pipelines and chains
- Testing async tasks in isolation

---

## Critical Patterns

### Pattern 1: Task File Structure

Every Django app that needs async work has a `tasks.py` at the app root. Tasks are thin wrappers that delegate to the service layer.

```python
# app_name/tasks.py
import structlog
from django.apps import apps
from django.utils.module_loading import import_string
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task

logger = structlog.get_logger('huey.tasks')
```

### Pattern 2: Tasks Call Services, Never Raw ORM

Tasks are THIN — they resolve the service via `import_string`, pass serializable arguments, and log entry/exit. All business logic lives in `services.py`.

```python
@db_task()
def process_document(*, document_id: int) -> None:
    logger.info('Init process document....')
    service = import_string('apps.api.services.process_document')
    service(document_id=document_id)
    logger.info('Finish process document....')
```

### Pattern 3: Lazy Imports via `import_string` or `apps.get_model`

Always use `import_string()` for services and `apps.get_model()` for models inside task bodies. This avoids circular imports and ensures Django apps are fully loaded.

```python
@db_task()
def send_report(*, item_list: list[int], requester_id: int) -> None:
    logger.info('Init send report....')
    requester = apps.get_model('user.User').objects.get(id=requester_id)
    service = import_string('apps.myapp.services.send_report')
    service(item_list=item_list, requester=requester)
    logger.info('Finish send report....')
```

### Pattern 4: Pass Only Serializable Arguments

NEVER pass model instances or querysets to tasks. Pass IDs (int), slugs (str), or simple collections (list[int], dict). Resolve objects inside the task body.

```python
# CORRECT — pass IDs
process_document(document_id=doc.id)

# WRONG — passes model instance (not serializable for Redis)
process_document(document=doc)
```

---

## Decision Tree

```
One-off async work (reports, file processing)?  -> @db_task()
Scheduled/recurring work (daily cleanup, cron)? -> @db_periodic_task(crontab(...))
Need to re-run same task after delay?            -> task.schedule(delay=seconds)
Need deduplication/locking?                      -> cache key guard pattern
Heavy batch that may need continuation?          -> self-schedule with delay after batch
```

---

## Code Examples

### Example 1: One-Off Async Task (`@db_task`)

```python
from huey.contrib.djhuey import db_task
import structlog

logger = structlog.get_logger('huey.tasks')

@db_task()
def process_payment_file(*, file_id_slug: str) -> None:
    logger.info('Init process payment file....')
    service = import_string('apps.api.services.process_payment_file')
    service(file_id_slug=file_id_slug)
    logger.info('Finish process payment file....')
```

Calling from a view or service:

```python
from .tasks import process_payment_file

def upload_handler(request):
    doc = Document.objects.create(file=request.FILES['file'])
    process_payment_file(file_id_slug=doc.id_slug)  # enqueued, returns immediately
```

### Example 2: Periodic Task (`@db_periodic_task`)

```python
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

@db_periodic_task(crontab(hour='5', minute='0'))
def update_overdue_payments() -> None:
    logger.info('Init update overdue payments....')
    payment_model = apps.get_model('operation.Payment')
    payment_model.objects.find_all_to_overdue().update(status='Vencido')
    logger.info('Finish update overdue payments....')
```

### Example 3: Task with Retry Configuration

```python
@db_task(retries=3, retry_delay=60)
def send_email_notification(*, notification_id: int) -> None:
    logger.info('Init send email notification....')
    service = import_string('apps.notification.services.send_email')
    service(notification_id=notification_id)
    logger.info('Finish send email notification....')
```

### Example 4: Cache-Based Deduplication Guard

Prevents overlapping runs of the same periodic task using a cache key.

```python
from django.core.cache import cache

@db_periodic_task(crontab(hour='3', minute='0'))
def save_payment_remissions() -> None:
    cache_key = 'save_payment_remissions_task_running'
    if cache.get(cache_key):
        return
    cache_timeout_seconds = 30
    cache.set(cache_key, value=True, timeout=cache_timeout_seconds)

    try:
        service = import_string('apps.operation.services.payment.create_payment_remission')
        # ... batch work ...
    except Exception:
        logger.exception('Error in save_payment_remissions task')
    finally:
        cache.delete(cache_key)
```

### Example 5: Self-Scheduling for Large Batches

When a task processes a batch but more items remain, it re-schedules itself with a delay.

```python
@db_periodic_task(crontab(hour='3', minute='0'))
def save_payment_remissions() -> None:
    # ... process batch ...
    if payment_model.objects.find_all_for_remission().exists():
        save_payment_remissions.schedule(delay=cache_timeout_seconds)
```

### Example 6: Task Pipelines

Chain tasks so the result of one feeds into the next.

```python
from huey.contrib.djhuey import db_task

@db_task()
def extract(file_id: int) -> dict:
    service = import_string('apps.api.services.extract_data')
    return service(file_id=file_id)

@db_task()
def transform(data: dict) -> dict:
    service = import_string('apps.api.services.transform_data')
    return service(data=data)

@db_task()
def load(data: dict) -> None:
    service = import_string('apps.api.services.load_data')
    service(data=data)

# Build pipeline
pipeline = extract.s(file_id=1).then(transform).then(load)
result = pipeline()
```

### Example 7: Task Priority

`PriorityRedisHuey` supports priority (lower number = higher priority, default 0).

```python
@db_task(priority=0)  # high priority (default)
def urgent_notification(*, user_id: int) -> None:
    ...

@db_task(priority=50)  # lower priority
def batch_report(*, report_id: int) -> None:
    ...
```

### Example 8: Signal Handling and Task Lifecycle

```python
from huey.signals import SIGNAL_COMPLETE, SIGNAL_ERROR, SIGNAL_EXECUTING
from huey.contrib.djhuey import signal

@signal(SIGNAL_EXECUTING)
def task_started(signal, task, exc=None):
    logger.info('Task started', task_id=task.id, task_name=task.name)

@signal(SIGNAL_COMPLETE)
def task_completed(signal, task, exc=None):
    logger.info('Task completed', task_id=task.id, task_name=task.name)

@signal(SIGNAL_ERROR)
def task_error(signal, task, exc=None):
    logger.error('Task failed', task_id=task.id, task_name=task.name, error=str(exc))
```

---

## Django Integration (`djhuey`)

### Settings Configuration

```python
# config/settings/huey.py
from multiprocessing import cpu_count

REDIS_URI = env('REDIS_URI', default='redis://localhost:6379')
HUEY_REDIS_DB = env('HUEY_REDIS_DB', default=4)
HUEY = {
    'huey_class': 'huey.PriorityRedisHuey',
    'utc': False,
    'connection': {'url': f'{REDIS_URI}/{HUEY_REDIS_DB}'},
    'immediate': False,
    'consumer': {
        'workers': cpu_count(),
    },
}
```

Key settings:
- `huey_class`: Use `PriorityRedisHuey` for priority support
- `utc: False`: Use local timezone for crontab schedules
- `immediate: False`: Queue tasks to Redis (set `True` in dev to run synchronously)
- `workers`: Number of consumer worker threads

### INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    'huey.contrib.djhuey',
    ...
]
```

### Logging

```python
# config/settings/structlog.py
DJANGO_HUEY_LOG_LEVEL = 'INFO'

LOGGING = {
    'loggers': {
        'huey': {'level': DJANGO_HUEY_LOG_LEVEL},
        'huey.tasks': {'level': DJANGO_HUEY_LOG_LEVEL},
    },
}
```

---

## Testing Async Tasks

### Strategy: Test Services Directly, Not Tasks

Tasks are thin wrappers. Test the service layer, not the Huey decorator.

```python
# tests/test_services.py
import pytest
from apps.myapp.services import process_document

@pytest.mark.django_db
def test_process_document(document_factory):
    doc = document_factory()
    process_document(document_id=doc.id)
    doc.refresh_from_db()
    assert doc.status == 'processed'
```

### Immediate Mode for Integration Tests

Set `immediate=True` in test settings so tasks execute synchronously.

```python
# config/settings/test.py
HUEY = {
    'huey_class': 'huey.PriorityRedisHuey',
    'immediate': True,
}
```

### Testing Task Enqueue (When Needed)

```python
from unittest.mock import patch

def test_upload_enqueues_task():
    with patch('apps.myapp.tasks.process_document') as mock_task:
        upload_handler(request)
        mock_task.assert_called_once_with(document_id=doc.id)
```

---

## Commands

```bash
python manage.py run_huey                  # start Huey consumer
python manage.py run_huey -w 4             # start with 4 workers
python manage.py run_huey -k thread        # thread-based workers (default)
python manage.py run_huey -k process       # process-based workers
python manage.py run_huey -k greenlet      # greenlet-based workers
python manage.py run_huey --flush-locks    # clear stale locks on startup
```

---

## Resources

- **Configuration**: See `config/settings/huey.py` for Redis backend setup
- **Task files**: Each app's `tasks.py` (e.g., `apps/operation/tasks.py`)
- **Service layer**: Each app's `services.py` — where task logic actually lives

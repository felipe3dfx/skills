# Huey — Django Setup & Configuration

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

## Advanced — Signal Handling

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

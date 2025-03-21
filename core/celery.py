from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from datetime import timedelta
from django.conf import settings

CELERY_IMPORTS=("")
CELERY_TASK_RESULT_EXPIRES = timedelta(days=3)
CELERY_TIMEZONE = 'UTC'
CELERYD_PREFETCH_MULTIPLIER = 0
CELERY_MAX_CACHED_RESULTS=1500
CELERY_TASK_PUBLISH_RETRY=True
CELERY_TASK_PUBLISH_RETRY_POLICY={
    'max_retries': 2,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.2,
}


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
broker_connection_retry_on_startup = True

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(
    worker_max_tasks_per_child=25,
    broker_pool_limit=None,
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# TERMINAL COMMANDS
# start the celery worker
# celery -A <proj_name>.celery worker -l info 

# start the celery beat
# celery -A your_project_name beat --loglevel=info

# view registered tasks
# celery -A <proj_name> inspect registered

# view scheduled tasks
# celery -A <proj_name> inspect scheduled

# view active tasks
# celery -A <proj_name> inspect active

# view reserved tasks
# celery -A <proj_name> inspect reserved

# If you're using Celery with Redis or RabbitMQ, you can install Flower to monitor queues in real-time.
# pip install flower
# celery -A <proj_name> flower



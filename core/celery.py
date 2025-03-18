from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
broker_connection_retry_on_startup = True

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks() 

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# TERMINAL COMMANDS
# start the celery worker
# celery -A <app_name>.celery worker -l info 

# start the celery beat
# celery -A <app_name> beat -l info
#!/bin/sh

set -o errexit
set -o nounset

rm -f './celerybeat.pid'
celery -A core beat -l info --pidfile /tmp/celerybeat.pid -s /tmp/celerybeat-schedule

#!/bin/sh

set -o errexit
set -o nounset

celery -A core worker -l info
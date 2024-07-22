from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from multiprocessing import set_start_method

# Set the start method to 'spawn' to avoid CUDA re-initialization issues
set_start_method("spawn", force=True)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

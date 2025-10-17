"""
ASGI config for cv_evaluator project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_evaluator.settings')

application = get_asgi_application()

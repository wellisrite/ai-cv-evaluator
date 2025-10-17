"""
WSGI config for cv_evaluator project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_evaluator.settings')

application = get_wsgi_application()

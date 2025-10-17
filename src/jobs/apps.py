"""
Jobs app configuration.
"""

from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'
    verbose_name = 'Job Management'
    
    def ready(self):
        """Initialize job management components when app is ready."""
        # Import signal handlers if any
        pass
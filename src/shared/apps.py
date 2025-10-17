"""
Shared app configuration.
"""

from django.apps import AppConfig


class SharedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shared'
    verbose_name = 'Shared Components'
    
    def ready(self):
        """Initialize shared components when app is ready."""
        # Import signal handlers if any
        pass
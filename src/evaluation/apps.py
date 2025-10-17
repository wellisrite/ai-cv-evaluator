"""
Evaluation app configuration.
"""

from django.apps import AppConfig


class EvaluationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'evaluation'
    verbose_name = 'CV Evaluation'
    
    def ready(self):
        """Initialize evaluation components when app is ready."""
        # Import signal handlers if any
        pass
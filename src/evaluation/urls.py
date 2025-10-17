"""
URL configuration for evaluation app.
"""
from django.urls import path
from . import views

app_name = 'evaluation'

urlpatterns = [
    # Document Management Endpoints
    path('documents/upload/', views.upload_documents, name='upload_documents'),
    
    # Evaluation Job Endpoints
    path('jobs/', views.list_evaluation_jobs, name='list_evaluation_jobs'),
    path('jobs/evaluate/', views.evaluate_documents, name='evaluate_documents'),
    path('jobs/<uuid:job_id>/result/', views.get_evaluation_result, name='get_evaluation_result'),
    
    # System Health Endpoints
    path('health/', views.health_check, name='health_check'),
]

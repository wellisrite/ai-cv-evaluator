"""
URL configuration for evaluation app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_documents, name='upload_documents'),
    path('evaluate/', views.evaluate_documents, name='evaluate_documents'),
    path('result/<uuid:job_id>/', views.get_evaluation_result, name='get_evaluation_result'),
    path('jobs/', views.list_evaluation_jobs, name='list_evaluation_jobs'),
    path('health/', views.health_check, name='health_check'),
]

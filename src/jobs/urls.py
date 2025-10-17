"""
URL routing for the jobs app.
"""

from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # Job management endpoints
    path('jobs/<uuid:job_id>/', views.get_job_status, name='job_status'),
    path('jobs/', views.list_jobs, name='list_jobs'),
    path('jobs/<uuid:job_id>/cancel/', views.cancel_job, name='cancel_job'),
    
    # Queue and worker management
    path('queues/status/', views.get_queue_status, name='queue_status'),
    path('workers/status/', views.get_worker_status, name='worker_status'),
    
    # Statistics and monitoring
    path('statistics/', views.get_job_statistics, name='job_statistics'),
]

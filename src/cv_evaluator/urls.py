"""
URL configuration for cv_evaluator project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# Import the essential views
from shared.views import upload_documents
from evaluation.views import evaluate_documents, get_evaluation_result
from jobs.views import list_evaluation_jobs


def api_root(request):
    """
    API root endpoint with only the 3 essential endpoints.
    """
    return JsonResponse({
        'message': 'CV Evaluator API',
        'version': '1.0.0',
        'endpoints': {
            'upload': '/api/upload/',
            'evaluate': '/api/evaluate/',
            'result': '/api/result/<job_id>/',
            'jobs': '/api/jobs/'
        }
    })


urlpatterns = [
    # Root endpoint
    path('', api_root, name='api_root'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Essential endpoints - these should work
    path('api/upload/', upload_documents, name='upload_documents'),
    path('api/evaluate/', evaluate_documents, name='evaluate_documents'),
    path('api/result/<uuid:job_id>/', get_evaluation_result, name='get_evaluation_result'),
    path('api/jobs/', list_evaluation_jobs, name='list_evaluation_jobs'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

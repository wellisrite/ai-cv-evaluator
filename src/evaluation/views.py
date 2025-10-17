"""
API views for the evaluation app.
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils import timezone
from shared.models import Document
from jobs.models import EvaluationJob
from .models import EvaluationResult
from .serializers import (
    DocumentSerializer, EvaluationJobSerializer, EvaluationResultSerializer,
    UploadSerializer, EvaluateSerializer
)
from .tasks import process_evaluation_job
from .logger import log_success, log_error, log_info
import uuid
 

@api_view(['POST'])
def evaluate_documents(request):
    """
    Start evaluation process for uploaded documents.
    
    Expected JSON data:
    {
        "job_title": "Backend Developer",
        "cv_document_id": "uuid",
        "project_document_id": "uuid"
    }
    """
    log_info("Evaluation request received", {
        "user_ip": request.META.get('REMOTE_ADDR'),
        "request_data": request.data
    })
    
    serializer = EvaluateSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Create evaluation job
            job = EvaluationJob.objects.create(
                job_title=serializer.validated_data['job_title'],
                cv_document_id=serializer.validated_data['cv_document_id'],
                project_document_id=serializer.validated_data['project_document_id']
            )
            
            log_info("Evaluation job created", {
                "job_id": str(job.id),
                "job_title": job.job_title,
                "cv_document_id": str(job.cv_document_id),
                "project_document_id": str(job.project_document_id)
            })
            
            # Queue evaluation job with Celery for async processing
            try:
                # Start the evaluation job asynchronously
                from .tasks import process_evaluation_job
                
                # Queue the job
                task = process_evaluation_job.delay(str(job.id))
                
                log_info("Evaluation job queued with Celery", {
                    "job_id": str(job.id),
                    "task_id": task.id,
                    "job_title": job.job_title
                })
                
            except Exception as celery_error:
                job.status = 'failed'
                job.error_message = f"Failed to queue evaluation job: {str(celery_error)}"
                job.save()
                
                log_error("Failed to queue evaluation job", exception=celery_error, extra_data={
                    "job_id": str(job.id),
                    "job_title": job.job_title
                })
                
                return Response({
                    'error': f'Failed to start evaluation: {str(celery_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            log_success("Evaluation job queued successfully", {"job_id": str(job.id)})
            
            return Response({
                'id': str(job.id),
                'status': 'queued'
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            log_error("Failed to create evaluation job", exception=e, extra_data={
                "job_title": serializer.validated_data.get('job_title', 'unknown'),
                "cv_document_id": str(serializer.validated_data.get('cv_document_id', 'unknown')),
                "project_document_id": str(serializer.validated_data.get('project_document_id', 'unknown'))
            })
            return Response({
                'error': f'Failed to start evaluation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    log_error("Evaluation request validation failed", extra_data={"errors": serializer.errors})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_evaluation_result(request, job_id):
    """
    Get evaluation result by job ID.
    
    Returns different responses based on job status:
    - queued/processing: basic status
    - completed: full results
    - failed: error message
    """
    log_info("Evaluation result request received", {
        "job_id": str(job_id),
        "user_ip": request.META.get('REMOTE_ADDR')
    })
    
    try:
        job = get_object_or_404(EvaluationJob, id=job_id)
        
        if job.status in ['queued', 'processing']:
            log_info("Evaluation result requested - job still processing", {
                "job_id": str(job.id),
                "status": job.status
            })
            return Response({
                'id': str(job.id),
                'status': job.status
            })
        
        elif job.status == 'completed':
            try:
                result = EvaluationResult.objects.get(job_id=job.id)
                log_success("Evaluation result retrieved successfully", {
                    "job_id": str(job.id),
                    "cv_match_rate": result.cv_match_rate,
                    "project_score": result.project_score
                })
                return Response({
                    'id': str(job.id),
                    'status': 'completed',
                    'result': {
                        'cv_match_rate': result.cv_match_rate,
                        'cv_feedback': result.cv_feedback,
                        'project_score': result.project_score,
                        'project_feedback': result.project_feedback,
                        'overall_summary': result.overall_summary,
                        'cv_detailed_scores': result.cv_detailed_scores,
                        'project_detailed_scores': result.project_detailed_scores
                    }
                })
            except EvaluationResult.DoesNotExist:
                log_error("Evaluation result not found for completed job", extra_data={
                    "job_id": str(job.id),
                    "status": job.status
                })
                return Response({
                    'id': str(job.id),
                    'status': 'processing'
                })
        
        elif job.status == 'failed':
            log_error("Evaluation result requested for failed job", extra_data={
                "job_id": str(job.id),
                "error_message": job.error_message
            })
            return Response({
                'id': str(job.id),
                'status': 'failed',
                'error': job.error_message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Http404:
        # Let the 404 from get_object_or_404 propagate
        raise
    except Exception as e:
        log_error("Failed to get evaluation result", exception=e, extra_data={
            "job_id": str(job_id)
        })
        return Response({
            'error': f'Failed to get evaluation result: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint.
    """
    log_info("Health check request received", {
        "user_ip": request.META.get('REMOTE_ADDR')
    })
    
    log_success("Health check completed", {
        "status": "healthy"
    })
    
    return Response({
        'status': 'healthy',
        'message': 'CV Evaluator API is running'
    })

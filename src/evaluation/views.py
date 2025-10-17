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
            
            # Run evaluation synchronously (bypassing Celery for now)
            try:
                # Run evaluation directly without Celery
                from .llm_evaluator import LLMEvaluator
                from .rag_system_safe import SafeRAGSystem
                from .tasks import extract_text_from_document
                
                # Update status to processing
                job.status = 'processing'
                job.started_at = timezone.now()
                job.save()
                
                # Initialize systems
                rag_system = SafeRAGSystem()
                llm_evaluator = LLMEvaluator()
                
                # Get document objects from IDs
                cv_document = Document.objects.get(id=job.cv_document_id)
                project_document = Document.objects.get(id=job.project_document_id)
                
                # Extract text from documents
                cv_text = extract_text_from_document(cv_document)
                project_text = extract_text_from_document(project_document)
                
                if not cv_text or not project_text:
                    raise ValueError("Could not extract text from documents")
                
                # Evaluate CV
                cv_result = llm_evaluator.evaluate_cv(cv_text, job.job_title)
                
                # Evaluate Project Report
                project_result = llm_evaluator.evaluate_project_report(project_text)
                
                # Generate overall summary
                overall_summary = llm_evaluator.generate_overall_summary(
                    cv_result, project_result, job.job_title
                )
                
                # Ensure we have valid results
                if not overall_summary:
                    overall_summary = "Evaluation completed but summary generation failed."
                if not cv_result:
                    cv_result = {"cv_match_rate": 0.0, "cv_feedback": "CV evaluation failed"}
                if not project_result:
                    project_result = {"project_score": 0.0, "project_feedback": "Project evaluation failed"}
                
                # Create evaluation result
                from .models import EvaluationResult
                result = EvaluationResult.objects.create(
                    job_id=job.id,
                    cv_match_rate=cv_result.get('cv_match_rate', 0.0),
                    cv_feedback=cv_result.get('cv_feedback', ''),
                    project_score=project_result.get('project_score', 0.0),
                    project_feedback=project_result.get('project_feedback', ''),
                    overall_summary=overall_summary,
                    cv_detailed_scores=cv_result,
                    project_detailed_scores=project_result
                )
                
                # Update job status
                job.status = 'completed'
                job.completed_at = timezone.now()
                job.save()
                
                log_success("Evaluation completed successfully", {
                    "job_id": str(job.id),
                    "cv_match_rate": result.cv_match_rate,
                    "project_score": result.project_score,
                    "processing_time": (job.completed_at - job.started_at).total_seconds() if job.started_at else None
                })
                
                
            except Exception as sync_error:
                job.status = 'failed'
                job.error_message = f"Evaluation failed: {str(sync_error)}"
                job.save()
                
                log_error("Evaluation failed during processing", exception=sync_error, extra_data={
                    "job_id": str(job.id),
                    "job_title": job.job_title
                })
                
                return Response({
                    'error': f'Failed to start evaluation: {str(sync_error)}'
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

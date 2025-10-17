"""
API views for the jobs app.
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import EvaluationJob, JobQueue, JobWorker, JobSchedule
from shared.utils import APIResponse, LoggingHelper
from shared.models import AuditLog
from evaluation.serializers import EvaluationJobSerializer
from evaluation.logger import log_success, log_error, log_info
import uuid


@api_view(['GET'])
def list_evaluation_jobs(request):
    """
    List all evaluation jobs with pagination.
    """
    log_info("List evaluation jobs request received", {
        "user_ip": request.META.get('REMOTE_ADDR')
    })
    
    try:
        jobs = EvaluationJob.objects.all().order_by('-created_at')
        serializer = EvaluationJobSerializer(jobs, many=True)
        
        log_success("Evaluation jobs listed successfully", {
            "total_jobs": len(serializer.data)
        })
        
        return Response(serializer.data)
    except Exception as e:
        log_error("Failed to list evaluation jobs", exception=e)
        return Response({
            'error': f'Failed to list jobs: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_job_status(request, job_id):
    """Get the status of a specific job."""
    try:
        job = get_object_or_404(EvaluationJob, id=job_id)
        
        # Log the request
        LoggingHelper.log_info(f"Job status requested", {
            "job_id": str(job_id),
            "status": job.status
        })
        
        response_data = {
            "id": str(job.id),
            "status": job.status,
            "job_title": job.job_title,
            "priority": job.priority,
            "queued_at": job.queued_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "processing_time": job.processing_time,
            "queue_time": job.queue_time,
            "retry_count": job.retry_count,
            "max_retries": job.max_retries,
        }
        
        if job.status == 'failed' and job.error_message:
            response_data["error_message"] = job.error_message
        
        if job.status == 'completed' and job.result_id:
            response_data["result_id"] = str(job.result_id)
        
        return APIResponse.success(response_data)
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to get job status", e, {"job_id": str(job_id)})
        return APIResponse.error(f"Failed to get job status: {str(e)}", status_code=500)


@api_view(['GET'])
def list_jobs(request):
    """List jobs with optional filtering."""
    try:
        # Get query parameters
        status_filter = request.GET.get('status')
        user_id = request.GET.get('user_id')
        limit = int(request.GET.get('limit', 20))
        offset = int(request.GET.get('offset', 0))
        
        # Build query
        jobs = EvaluationJob.objects.all()
        
        if status_filter:
            jobs = jobs.filter(status=status_filter)
        
        if user_id:
            jobs = jobs.filter(user_id=user_id)
        
        # Apply pagination
        total_count = jobs.count()
        jobs = jobs.order_by('-queued_at')[offset:offset + limit]
        
        # Serialize jobs
        jobs_data = []
        for job in jobs:
            job_data = {
                "id": str(job.id),
                "status": job.status,
                "job_title": job.job_title,
                "priority": job.priority,
                "queued_at": job.queued_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "processing_time": job.processing_time,
                "queue_time": job.queue_time,
            }
            jobs_data.append(job_data)
        
        response_data = {
            "jobs": jobs_data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
        LoggingHelper.log_info(f"Jobs listed", {
            "total_count": total_count,
            "returned_count": len(jobs_data),
            "filters": {"status": status_filter, "user_id": user_id}
        })
        
        return APIResponse.success(response_data)
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to list jobs", e)
        return APIResponse.error(f"Failed to list jobs: {str(e)}", status_code=500)


@api_view(['POST'])
def cancel_job(request, job_id):
    """Cancel a job if it's still queued or processing."""
    try:
        job = get_object_or_404(EvaluationJob, id=job_id)
        
        if job.status in ['completed', 'failed', 'cancelled']:
            return APIResponse.error("Job cannot be cancelled in its current status", status_code=400)
        
        job.status = 'cancelled'
        job.completed_at = timezone.now()
        job.error_message = "Job cancelled by user"
        job.save()
        
        # Log the cancellation
        LoggingHelper.log_info(f"Job cancelled", {
            "job_id": str(job_id),
            "previous_status": job.status
        })
        
        # Create audit log
        AuditLog.objects.create(
            event_type='user_action',
            event_name='job_cancelled',
            user_id=request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
            resource_id=job_id,
            resource_type='evaluation_job',
            details={"job_title": job.job_title}
        )
        
        return APIResponse.success({"message": "Job cancelled successfully"})
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to cancel job", e, {"job_id": str(job_id)})
        return APIResponse.error(f"Failed to cancel job: {str(e)}", status_code=500)


@api_view(['GET'])
def get_queue_status(request):
    """Get the status of job queues."""
    try:
        queues = JobQueue.objects.filter(is_active=True)
        
        queue_data = []
        for queue in queues:
            queue_info = {
                "name": queue.name,
                "type": queue.queue_type,
                "current_size": queue.current_size,
                "max_queue_size": queue.max_queue_size,
                "total_processed": queue.total_processed,
                "total_failed": queue.total_failed,
                "success_rate": queue.success_rate,
                "is_active": queue.is_active
            }
            queue_data.append(queue_info)
        
        LoggingHelper.log_info(f"Queue status requested", {"queue_count": len(queue_data)})
        
        return APIResponse.success({"queues": queue_data})
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to get queue status", e)
        return APIResponse.error(f"Failed to get queue status: {str(e)}", status_code=500)


@api_view(['GET'])
def get_worker_status(request):
    """Get the status of job workers."""
    try:
        workers = JobWorker.objects.all()
        
        worker_data = []
        for worker in workers:
            worker_info = {
                "worker_id": worker.worker_id,
                "worker_name": worker.worker_name,
                "status": worker.status,
                "hostname": worker.hostname,
                "ip_address": str(worker.ip_address),
                "current_job_id": str(worker.current_job_id) if worker.current_job_id else None,
                "jobs_processed": worker.jobs_processed,
                "jobs_failed": worker.jobs_failed,
                "last_heartbeat": worker.last_heartbeat,
                "is_online": worker.is_online()
            }
            worker_data.append(worker_info)
        
        LoggingHelper.log_info(f"Worker status requested", {"worker_count": len(worker_data)})
        
        return APIResponse.success({"workers": worker_data})
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to get worker status", e)
        return APIResponse.error(f"Failed to get worker status: {str(e)}", status_code=500)


@api_view(['GET'])
def get_job_statistics(request):
    """Get job processing statistics."""
    try:
        from django.db.models import Count, Avg, Q
        from datetime import timedelta
        
        # Time ranges
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Overall statistics
        total_jobs = EvaluationJob.objects.count()
        completed_jobs = EvaluationJob.objects.filter(status='completed').count()
        failed_jobs = EvaluationJob.objects.filter(status='failed').count()
        processing_jobs = EvaluationJob.objects.filter(status='processing').count()
        queued_jobs = EvaluationJob.objects.filter(status='queued').count()
        
        # Time-based statistics
        jobs_24h = EvaluationJob.objects.filter(queued_at__gte=last_24h).count()
        jobs_7d = EvaluationJob.objects.filter(queued_at__gte=last_7d).count()
        jobs_30d = EvaluationJob.objects.filter(queued_at__gte=last_30d).count()
        
        # Average processing times
        completed_jobs_with_time = EvaluationJob.objects.filter(
            status='completed',
            started_at__isnull=False,
            completed_at__isnull=False
        )
        
        avg_processing_time = None
        if completed_jobs_with_time.exists():
            # Calculate average processing time
            total_time = 0
            count = 0
            for job in completed_jobs_with_time:
                if job.processing_time:
                    total_time += job.processing_time
                    count += 1
            if count > 0:
                avg_processing_time = total_time / count
        
        statistics = {
            "overall": {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "processing_jobs": processing_jobs,
                "queued_jobs": queued_jobs,
                "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            },
            "time_based": {
                "last_24h": jobs_24h,
                "last_7d": jobs_7d,
                "last_30d": jobs_30d
            },
            "performance": {
                "avg_processing_time_seconds": avg_processing_time
            }
        }
        
        LoggingHelper.log_info(f"Job statistics requested", {"total_jobs": total_jobs})
        
        return APIResponse.success(statistics)
        
    except Exception as e:
        LoggingHelper.log_error(f"Failed to get job statistics", e)
        return APIResponse.error(f"Failed to get job statistics: {str(e)}", status_code=500)
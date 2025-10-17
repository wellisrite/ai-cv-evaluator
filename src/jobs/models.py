"""
Job management models for the CV Evaluation system.
This app handles all job-related operations and can be split into a separate microservice.
"""

import uuid
from django.db import models
from django.utils import timezone
from shared.models import BaseModel


class EvaluationJob(BaseModel):
    """Model for tracking evaluation jobs."""
    
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Job identification
    job_title = models.CharField(max_length=255)
    job_type = models.CharField(max_length=50, default='cv_evaluation')
    
    # Document references (UUIDs to shared documents)
    cv_document_id = models.UUIDField()
    project_document_id = models.UUIDField()
    
    # Job status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Timing fields
    queued_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # User and request tracking
    user_id = models.UUIDField(null=True, blank=True)
    request_id = models.UUIDField(default=uuid.uuid4, editable=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    # Job configuration
    config = models.JSONField(default=dict, help_text="Job-specific configuration")
    
    # Error handling
    error_message = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # Results reference
    result_id = models.UUIDField(null=True, blank=True)
    
    class Meta:
        db_table = 'jobs_evaluation_job'
        ordering = ['-queued_at']
        indexes = [
            models.Index(fields=['status', 'queued_at']),
            models.Index(fields=['user_id', 'queued_at']),
            models.Index(fields=['priority', 'status']),
        ]
    
    def __str__(self):
        return f"Job {self.id} - {self.job_title} ({self.status})"
    
    @property
    def processing_time(self):
        """Calculate processing time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def queue_time(self):
        """Calculate queue time in seconds."""
        if self.started_at:
            return (self.started_at - self.queued_at).total_seconds()
        return None
    
    def can_retry(self):
        """Check if job can be retried."""
        return self.retry_count < self.max_retries and self.status == 'failed'
    
    def mark_started(self):
        """Mark job as started."""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self, result_id=None):
        """Mark job as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if result_id:
            self.result_id = result_id
        self.save(update_fields=['status', 'completed_at', 'result_id'])
    
    def mark_failed(self, error_message=None):
        """Mark job as failed."""
        self.status = 'failed'
        self.completed_at = timezone.now()
        if error_message:
            self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])


class JobQueue(BaseModel):
    """Model for managing job queues."""
    
    QUEUE_TYPES = [
        ('evaluation', 'Evaluation Queue'),
        ('notification', 'Notification Queue'),
        ('cleanup', 'Cleanup Queue'),
        ('reporting', 'Reporting Queue'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    queue_type = models.CharField(max_length=50, choices=QUEUE_TYPES)
    description = models.TextField(blank=True)
    
    # Queue configuration
    max_workers = models.IntegerField(default=4)
    max_queue_size = models.IntegerField(default=1000)
    is_active = models.BooleanField(default=True)
    
    # Queue statistics
    current_size = models.IntegerField(default=0)
    total_processed = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    
    # Configuration
    config = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'jobs_job_queue'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.queue_type})"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage."""
        total = self.total_processed + self.total_failed
        if total == 0:
            return 0
        return (self.total_processed / total) * 100


class JobWorker(BaseModel):
    """Model for tracking job workers."""
    
    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
        ('error', 'Error'),
    ]
    
    worker_id = models.CharField(max_length=100, unique=True)
    worker_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    
    # Worker information
    hostname = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    process_id = models.IntegerField()
    
    # Current job
    current_job_id = models.UUIDField(null=True, blank=True)
    current_job_started_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    jobs_processed = models.IntegerField(default=0)
    jobs_failed = models.IntegerField(default=0)
    last_heartbeat = models.DateTimeField(auto_now=True)
    
    # Configuration
    config = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'jobs_job_worker'
        ordering = ['-last_heartbeat']
        indexes = [
            models.Index(fields=['status', 'last_heartbeat']),
            models.Index(fields=['worker_id']),
        ]
    
    def __str__(self):
        return f"{self.worker_name} ({self.status})"
    
    def update_heartbeat(self):
        """Update worker heartbeat."""
        self.last_heartbeat = timezone.now()
        self.save(update_fields=['last_heartbeat'])
    
    def is_online(self, timeout_minutes=5):
        """Check if worker is online based on heartbeat."""
        if not self.last_heartbeat:
            return False
        timeout = timezone.now() - timezone.timedelta(minutes=timeout_minutes)
        return self.last_heartbeat > timeout


class JobSchedule(BaseModel):
    """Model for scheduled jobs."""
    
    SCHEDULE_TYPES = [
        ('once', 'Run Once'),
        ('interval', 'Interval'),
        ('cron', 'Cron Expression'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES)
    
    # Schedule configuration
    schedule_config = models.JSONField(default=dict)
    job_config = models.JSONField(default=dict)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_runs = models.IntegerField(default=0)
    successful_runs = models.IntegerField(default=0)
    failed_runs = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'jobs_job_schedule'
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'next_run']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.schedule_type})"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage."""
        if self.total_runs == 0:
            return 0
        return (self.successful_runs / self.total_runs) * 100
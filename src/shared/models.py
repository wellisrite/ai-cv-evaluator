"""
Shared models and base classes for the CV Evaluation system.
These models are designed to be used across multiple microservices.
"""

import uuid
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Base model with common fields for all models."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Document(BaseModel):
    """Shared document model for file storage."""
    
    DOCUMENT_TYPES = [
        ('cv', 'CV'),
        ('project_report', 'Project Report'),
        ('job_description', 'Job Description'),
        ('case_study_brief', 'Case Study Brief'),
        ('cv_rubric', 'CV Scoring Rubric'),
        ('project_rubric', 'Project Scoring Rubric'),
    ]
    
    file = models.FileField(upload_to='documents/')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    uploaded_by = models.UUIDField(null=True, blank=True, help_text="User ID who uploaded the document")
    
    class Meta:
        db_table = 'shared_document'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.filename}"


class AuditLog(BaseModel):
    """Audit log for tracking system events."""
    
    EVENT_TYPES = [
        ('user_action', 'User Action'),
        ('system_event', 'System Event'),
        ('api_call', 'API Call'),
        ('error', 'Error'),
        ('evaluation', 'Evaluation'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    event_name = models.CharField(max_length=255)
    user_id = models.UUIDField(null=True, blank=True)
    resource_id = models.UUIDField(null=True, blank=True)
    resource_type = models.CharField(max_length=100, null=True, blank=True)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'shared_audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['resource_id', 'resource_type']),
        ]
    
    def __str__(self):
        return f"{self.event_type}: {self.event_name} at {self.created_at}"


class SystemConfig(BaseModel):
    """System configuration settings."""
    
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_encrypted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'shared_system_config'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."


class HealthCheck(BaseModel):
    """Health check records for monitoring."""
    
    SERVICE_TYPES = [
        ('api', 'API Service'),
        ('worker', 'Worker Service'),
        ('database', 'Database'),
        ('redis', 'Redis'),
        ('llm', 'LLM Service'),
        ('vector_db', 'Vector Database'),
    ]
    
    STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('unhealthy', 'Unhealthy'),
        ('degraded', 'Degraded'),
    ]
    
    service_name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    response_time_ms = models.FloatField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'shared_health_check'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['service_name', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.service_name}: {self.status}"
from django.db import models
from django.utils import timezone
import uuid


class Document(models.Model):
    """Model to store uploaded documents (CV, Project Report, etc.)"""
    DOCUMENT_TYPES = [
        ('cv', 'Candidate CV'),
        ('project_report', 'Project Report'),
        ('job_description', 'Job Description'),
        ('case_study_brief', 'Case Study Brief'),
        ('cv_rubric', 'CV Scoring Rubric'),
        ('project_rubric', 'Project Scoring Rubric'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='documents/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(default=timezone.now)
    file_size = models.BigIntegerField()
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.filename}"


class EvaluationJob(models.Model):
    """Model to track evaluation jobs"""
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_title = models.CharField(max_length=255)
    cv_document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='cv_evaluations')
    project_document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='project_evaluations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Evaluation Job {self.id} - {self.job_title}"


class EvaluationResult(models.Model):
    """Model to store evaluation results"""
    job = models.OneToOneField(EvaluationJob, on_delete=models.CASCADE, related_name='result')
    
    # CV Evaluation Results
    cv_match_rate = models.FloatField(null=True, blank=True)
    cv_feedback = models.TextField(blank=True)
    
    # Project Evaluation Results
    project_score = models.FloatField(null=True, blank=True)
    project_feedback = models.TextField(blank=True)
    
    # Overall Results
    overall_summary = models.TextField(blank=True)
    
    # Detailed Scoring (stored as JSON for flexibility)
    cv_detailed_scores = models.JSONField(default=dict, blank=True)
    project_detailed_scores = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Result for Job {self.job.id}"

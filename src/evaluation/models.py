"""
Evaluation-specific models for the CV Evaluation system.
This app handles the core evaluation logic and can be split into a separate microservice.
"""

import uuid
from django.db import models
from django.utils import timezone
from shared.models import BaseModel


class EvaluationResult(BaseModel):
    """Model for storing evaluation results."""
    
    # Job reference
    job_id = models.UUIDField(unique=True, help_text="Reference to the evaluation job")
    
    # CV Evaluation Results
    cv_match_rate = models.FloatField(help_text="CV match rate (0.0 to 1.0)")
    cv_feedback = models.TextField(help_text="Detailed CV feedback")
    cv_detailed_scores = models.JSONField(default=dict, help_text="Detailed CV scoring breakdown")
    
    # Project Evaluation Results
    project_score = models.FloatField(help_text="Project score (1.0 to 5.0)")
    project_feedback = models.TextField(help_text="Detailed project feedback")
    project_detailed_scores = models.JSONField(default=dict, help_text="Detailed project scoring breakdown")
    
    # Overall Results
    overall_summary = models.TextField(help_text="Overall evaluation summary")
    overall_score = models.FloatField(null=True, blank=True, help_text="Combined overall score")
    
    # Evaluation metadata
    evaluation_version = models.CharField(max_length=20, default='1.0')
    evaluation_config = models.JSONField(default=dict, help_text="Configuration used for evaluation")
    
    # Processing information
    processing_time_seconds = models.FloatField(null=True, blank=True)
    llm_model_used = models.CharField(max_length=100, blank=True)
    rag_system_used = models.CharField(max_length=50, default='chromadb')
    
    class Meta:
        db_table = 'evaluation_evaluation_result'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['job_id']),
            models.Index(fields=['cv_match_rate']),
            models.Index(fields=['project_score']),
            models.Index(fields=['overall_score']),
        ]
    
    def __str__(self):
        return f"Result for Job {self.job_id} - CV: {self.cv_match_rate:.2f}, Project: {self.project_score:.2f}"
    
    @property
    def is_high_performer(self):
        """Check if this is a high-performing candidate."""
        return self.cv_match_rate >= 0.8 and self.project_score >= 4.0
    
    @property
    def is_qualified(self):
        """Check if candidate meets minimum qualifications."""
        return self.cv_match_rate >= 0.6 and self.project_score >= 3.0


class EvaluationTemplate(BaseModel):
    """Templates for different types of evaluations."""
    
    TEMPLATE_TYPES = [
        ('cv_evaluation', 'CV Evaluation'),
        ('project_evaluation', 'Project Evaluation'),
        ('combined_evaluation', 'Combined Evaluation'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    
    # Template configuration
    prompts = models.JSONField(default=dict, help_text="LLM prompts for this template")
    scoring_criteria = models.JSONField(default=dict, help_text="Scoring criteria and weights")
    evaluation_config = models.JSONField(default=dict, help_text="Evaluation configuration")
    
    # Template status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    version = models.CharField(max_length=20, default='1.0')
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'evaluation_evaluation_template'
        ordering = ['name']
        indexes = [
            models.Index(fields=['template_type', 'is_active']),
            models.Index(fields=['is_default']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"
    
    def increment_usage(self):
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])


class EvaluationMetric(BaseModel):
    """Metrics for tracking evaluation performance."""
    
    METRIC_TYPES = [
        ('accuracy', 'Accuracy'),
        ('precision', 'Precision'),
        ('recall', 'Recall'),
        ('f1_score', 'F1 Score'),
        ('processing_time', 'Processing Time'),
        ('user_satisfaction', 'User Satisfaction'),
    ]
    
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    metric_name = models.CharField(max_length=255)
    value = models.FloatField()
    
    # Context information
    evaluation_template_id = models.UUIDField(null=True, blank=True)
    job_id = models.UUIDField(null=True, blank=True)
    user_id = models.UUIDField(null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'evaluation_evaluation_metric'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['metric_type', 'created_at']),
            models.Index(fields=['evaluation_template_id']),
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.value}"


class EvaluationFeedback(BaseModel):
    """User feedback on evaluation results."""
    
    FEEDBACK_TYPES = [
        ('accuracy', 'Accuracy Feedback'),
        ('usefulness', 'Usefulness Feedback'),
        ('clarity', 'Clarity Feedback'),
        ('completeness', 'Completeness Feedback'),
    ]
    
    RATING_CHOICES = [
        (1, 'Very Poor'),
        (2, 'Poor'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    
    # References
    evaluation_result_id = models.UUIDField()
    user_id = models.UUIDField()
    
    # Feedback details
    feedback_type = models.CharField(max_length=50, choices=FEEDBACK_TYPES)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    
    # Additional context
    context = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'evaluation_evaluation_feedback'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['evaluation_result_id']),
            models.Index(fields=['user_id', 'feedback_type']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"Feedback for Result {self.evaluation_result_id}: {self.rating}/5"


class EvaluationBatch(BaseModel):
    """Batch processing for multiple evaluations."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Batch configuration
    template_id = models.UUIDField(null=True, blank=True)
    batch_config = models.JSONField(default=dict)
    
    # Progress tracking
    total_jobs = models.IntegerField(default=0)
    completed_jobs = models.IntegerField(default=0)
    failed_jobs = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    batch_results = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'evaluation_evaluation_batch'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Batch {self.name} ({self.status})"
    
    @property
    def progress_percentage(self):
        """Calculate batch progress percentage."""
        if self.total_jobs == 0:
            return 0
        return (self.completed_jobs / self.total_jobs) * 100
    
    @property
    def success_rate(self):
        """Calculate batch success rate."""
        total_processed = self.completed_jobs + self.failed_jobs
        if total_processed == 0:
            return 0
        return (self.completed_jobs / total_processed) * 100
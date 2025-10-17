from django.contrib import admin
from shared.models import Document
from jobs.models import EvaluationJob
from .models import EvaluationResult


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'document_type', 'file_size', 'created_at']
    list_filter = ['document_type', 'created_at']
    search_fields = ['filename']


@admin.register(EvaluationJob)
class EvaluationJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'job_title', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['job_title']
    readonly_fields = ['id', 'created_at', 'started_at', 'completed_at']


@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = ['job_id', 'cv_match_rate', 'project_score', 'created_at']
    readonly_fields = ['created_at']

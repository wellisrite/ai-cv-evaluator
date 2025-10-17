"""
Serializers for the evaluation app.
"""
from rest_framework import serializers
from shared.models import Document
from jobs.models import EvaluationJob
from .models import EvaluationResult


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    
    class Meta:
        model = Document
        fields = ['id', 'document_type', 'filename', 'file_size', 'created_at']
        read_only_fields = ['id', 'created_at']


class EvaluationJobSerializer(serializers.ModelSerializer):
    """Serializer for EvaluationJob model."""
    cv_document_id = serializers.UUIDField(read_only=True)
    project_document_id = serializers.UUIDField(read_only=True)
    
    class Meta:
        model = EvaluationJob
        fields = ['id', 'job_title', 'cv_document_id', 'project_document_id', 
                 'status', 'created_at', 'started_at', 'completed_at', 'error_message']
        read_only_fields = ['id', 'created_at', 'started_at', 'completed_at', 'error_message']


class EvaluationResultSerializer(serializers.ModelSerializer):
    """Serializer for EvaluationResult model."""
    
    class Meta:
        model = EvaluationResult
        fields = ['cv_match_rate', 'cv_feedback', 'project_score', 'project_feedback',
                 'overall_summary', 'cv_detailed_scores', 'project_detailed_scores', 'created_at']
        read_only_fields = ['created_at']


class UploadSerializer(serializers.Serializer):
    """Serializer for file uploads."""
    cv_file = serializers.FileField()
    project_file = serializers.FileField()
    
    def validate_cv_file(self, value):
        """Validate CV file."""
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("CV file must be a PDF")
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("CV file size must be less than 10MB")
        return value
    
    def validate_project_file(self, value):
        """Validate project file."""
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Project file must be a PDF")
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("Project file size must be less than 10MB")
        return value


class EvaluateSerializer(serializers.Serializer):
    """Serializer for evaluation requests."""
    job_title = serializers.CharField(max_length=255)
    cv_document_id = serializers.UUIDField()
    project_document_id = serializers.UUIDField()
    
    def validate_cv_document_id(self, value):
        """Validate CV document exists."""
        try:
            from shared.models import Document
            doc = Document.objects.get(id=value, document_type='cv')
            return value
        except Document.DoesNotExist:
            raise serializers.ValidationError("CV document not found")
    
    def validate_project_document_id(self, value):
        """Validate project document exists."""
        try:
            from shared.models import Document
            doc = Document.objects.get(id=value, document_type='project_report')
            return value
        except Document.DoesNotExist:
            raise serializers.ValidationError("Project document not found")

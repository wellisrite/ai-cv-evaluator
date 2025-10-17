"""
Shared views for common functionality across the application.
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Document
from evaluation.serializers import UploadSerializer
from evaluation.logger import log_success, log_error, log_info


@api_view(['POST'])
def upload_documents(request):
    """
    Upload CV and project report documents.
    
    Expected form data:
    - cv_file: PDF file
    - project_file: PDF file
    """
    log_info("Document upload request received", {"user_ip": request.META.get('REMOTE_ADDR')})
    
    serializer = UploadSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            # Save CV document
            cv_file = serializer.validated_data['cv_file']
            cv_document = Document.objects.create(
                document_type='cv',
                file=cv_file,
                filename=cv_file.name,
                file_size=cv_file.size
            )
            
            # Save project document
            project_file = serializer.validated_data['project_file']
            project_document = Document.objects.create(
                document_type='project_report',
                file=project_file,
                filename=project_file.name,
                file_size=project_file.size
            )
            
            log_success("Documents uploaded successfully", {
                "cv_document_id": str(cv_document.id),
                "project_document_id": str(project_document.id),
                "cv_filename": cv_file.name,
                "project_filename": project_file.name
            })
            
            return Response({
                'cv_document_id': str(cv_document.id),
                'project_document_id': str(project_document.id),
                'message': 'Documents uploaded successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            log_error("Failed to upload documents", exception=e, extra_data={
                "cv_filename": serializer.validated_data.get('cv_file', {}).get('name', 'unknown'),
                "project_filename": serializer.validated_data.get('project_file', {}).get('name', 'unknown')
            })
            return Response({
                'error': f'Failed to upload documents: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    log_error("Document upload validation failed", extra_data={"errors": serializer.errors})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

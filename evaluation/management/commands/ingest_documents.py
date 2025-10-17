"""
Django management command to ingest system documents into the vector database.
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from evaluation.models import Document
from evaluation.tasks import ingest_system_documents
from evaluation.logger import log_success, log_error, log_info
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Ingest system documents (job description, case study brief, rubrics) into the vector database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-ingestion even if documents already exist',
        )

    def handle(self, *args, **options):
        log_info("Document ingestion command started", {
            "force": options.get('force', False)
        })
        self.stdout.write('Starting document ingestion...')
        
        # Check if database is ready
        try:
            from django.db import connection
            connection.ensure_connection()
            log_success("Database connection verified")
            self.stdout.write('✅ Database connection verified')
        except Exception as e:
            log_error("Database connection failed", exception=e)
            self.stdout.write(
                self.style.ERROR(f'❌ Database not ready: {e}')
            )
            return
        
        # Define document mappings
        documents_to_ingest = [
            {
                'filename': 'job_description.md',
                'document_type': 'job_description',
                'path': 'sample_documents/job_description.md'
            },
            {
                'filename': 'case_study_brief.md',
                'document_type': 'case_study_brief',
                'path': 'sample_documents/case_study_brief.md'
            },
            {
                'filename': 'cv_scoring_rubric.md',
                'document_type': 'cv_rubric',
                'path': 'sample_documents/cv_scoring_rubric.md'
            },
            {
                'filename': 'project_scoring_rubric.md',
                'document_type': 'project_rubric',
                'path': 'sample_documents/project_scoring_rubric.md'
            }
        ]
        
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        
        for doc_info in documents_to_ingest:
            file_path = base_dir / doc_info['path']
            
            if not file_path.exists():
                log_error("Document file not found", extra_data={
                    "filename": doc_info['filename'],
                    "path": str(file_path)
                })
                self.stdout.write(
                    self.style.WARNING(f'File not found: {file_path}')
                )
                continue
            
            # Check if document already exists
            existing_doc = Document.objects.filter(
                document_type=doc_info['document_type'],
                filename=doc_info['filename']
            ).first()
            
            if existing_doc and not options['force']:
                log_info("Document already exists, skipping", {
                    "filename": doc_info['filename'],
                    "document_type": doc_info['document_type']
                })
                self.stdout.write(
                    self.style.WARNING(
                        f'Document {doc_info["filename"]} already exists. Use --force to re-ingest.'
                    )
                )
                continue
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create or update document
            if existing_doc and options['force']:
                log_info("Force re-ingesting document", {
                    "filename": doc_info['filename'],
                    "document_type": doc_info['document_type']
                })
                existing_doc.file.delete(save=False)  # Delete old file
                existing_doc.delete()
            
            # Create new document
            django_file = ContentFile(content.encode('utf-8'), name=doc_info['filename'])
            document = Document.objects.create(
                document_type=doc_info['document_type'],
                file=django_file,
                filename=doc_info['filename'],
                file_size=len(content.encode('utf-8'))
            )
            
            log_success("Document created successfully", {
                "filename": doc_info['filename'],
                "document_type": doc_info['document_type'],
                "file_size": len(content.encode('utf-8')),
                "document_id": str(document.id)
            })
            
            self.stdout.write(
                self.style.SUCCESS(f'Created document: {doc_info["filename"]}')
            )
        
        # Trigger document ingestion into vector database
        log_info("Triggering vector database ingestion")
        self.stdout.write('Triggering vector database ingestion...')
        try:
            result = ingest_system_documents.delay()
            log_success("Document ingestion task started", {
                "task_id": result.id
            })
            self.stdout.write(
                self.style.SUCCESS(f'Document ingestion task started: {result.id}')
            )
            self.stdout.write(
                'You can check the task status in the Celery worker logs.'
            )
        except Exception as e:
            log_error("Celery task failed, falling back to synchronous execution", exception=e)
            self.stdout.write(
                self.style.WARNING(f'Celery task failed: {e}')
            )
            self.stdout.write(
                'Running document ingestion synchronously...'
            )
            # Run ingestion synchronously as fallback
            try:
                from .tasks import ingest_system_documents
                result = ingest_system_documents()
                log_success("Synchronous document ingestion completed", {
                    "result": result
                })
                self.stdout.write(
                    self.style.SUCCESS(f'Synchronous ingestion completed: {result}')
                )
            except Exception as sync_error:
                log_error("Synchronous document ingestion failed", exception=sync_error)
                self.stdout.write(
                    self.style.ERROR(f'Synchronous ingestion also failed: {sync_error}')
                )

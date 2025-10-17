"""
Celery tasks for async evaluation processing.
"""
from celery import shared_task
from django.utils import timezone
from .models import EvaluationJob, EvaluationResult, Document
from .rag_system_safe import SafeRAGSystem
from .llm_evaluator import LLMEvaluator
from .logger import log_success, log_error, log_info
import os


@shared_task(bind=True, max_retries=3)
def process_evaluation_job(self, job_id: str):
    """Process an evaluation job asynchronously."""
    log_info("Starting evaluation job processing", {"job_id": job_id})
    
    try:
        # Get the evaluation job
        job = EvaluationJob.objects.get(id=job_id)
        
        # Update status to processing
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save()
        
        log_info("Evaluation job status updated to processing", {
            "job_id": job_id,
            "job_title": job.job_title
        })
        
        # Initialize systems
        rag_system = SafeRAGSystem()
        llm_evaluator = LLMEvaluator()
        
        # Extract text from documents
        log_info("Extracting text from documents", {"job_id": job_id})
        cv_text = extract_text_from_document(job.cv_document)
        project_text = extract_text_from_document(job.project_document)
        
        if not cv_text or not project_text:
            raise ValueError("Could not extract text from documents")
        
        log_info("Text extraction completed", {
            "job_id": job_id,
            "cv_text_length": len(cv_text),
            "project_text_length": len(project_text)
        })
        
        # Evaluate CV
        log_info("Starting CV evaluation", {"job_id": job_id})
        cv_result = llm_evaluator.evaluate_cv(cv_text, job.job_title)
        log_success("CV evaluation completed", {
            "job_id": job_id,
            "cv_match_rate": cv_result.get('cv_match_rate', 0.0)
        })
        
        # Evaluate Project Report
        log_info("Starting project report evaluation", {"job_id": job_id})
        project_result = llm_evaluator.evaluate_project_report(project_text)
        log_success("Project report evaluation completed", {
            "job_id": job_id,
            "project_score": project_result.get('project_score', 0.0)
        })
        
        # Generate overall summary
        log_info("Generating overall summary", {"job_id": job_id})
        overall_summary = llm_evaluator.generate_overall_summary(
            cv_result, project_result, job.job_title
        )
        log_success("Overall summary generated", {"job_id": job_id})
        
        # Create evaluation result
        result = EvaluationResult.objects.create(
            job=job,
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
        
        log_success("Evaluation job completed successfully", {
            "job_id": job_id,
            "cv_match_rate": result.cv_match_rate,
            "project_score": result.project_score,
            "processing_time": (job.completed_at - job.started_at).total_seconds() if job.started_at else None
        })
        
        return f"Evaluation completed successfully for job {job_id}"
        
    except Exception as exc:
        log_error("Evaluation job failed", exception=exc, extra_data={
            "job_id": job_id,
            "retry_count": self.request.retries
        })
        
        # Update job status to failed
        try:
            job = EvaluationJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(exc)
            job.completed_at = timezone.now()
            job.save()
        except:
            pass
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            log_info("Retrying evaluation job", {
                "job_id": job_id,
                "retry_count": self.request.retries + 1,
                "max_retries": self.max_retries
            })
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        else:
            log_error("Evaluation job failed permanently", exception=exc, extra_data={
                "job_id": job_id,
                "max_retries_reached": True
            })
            raise exc


@shared_task
def ingest_system_documents():
    """Ingest system documents (job description, case study brief, rubrics) into vector DB."""
    log_info("Starting system documents ingestion")
    
    try:
        rag_system = SafeRAGSystem()
        
        # Get system documents
        system_docs = Document.objects.filter(
            document_type__in=['job_description', 'case_study_brief', 'cv_rubric', 'project_rubric']
        )
        
        log_info("Found system documents to ingest", {
            "document_count": system_docs.count(),
            "document_types": list(system_docs.values_list('document_type', flat=True))
        })
        
        ingested_count = 0
        for doc in system_docs:
            try:
                chunks = rag_system.ingest_document(
                    file_path=doc.file.path,
                    document_type=doc.document_type,
                    document_id=str(doc.id)
                )
                ingested_count += chunks
                log_success("Document ingested successfully", {
                    "filename": doc.filename,
                    "document_type": doc.document_type,
                    "chunks_ingested": chunks
                })
            except Exception as e:
                log_error("Error ingesting document", exception=e, extra_data={
                    "filename": doc.filename,
                    "document_type": doc.document_type
                })
        
        log_success("System documents ingestion completed", {
            "total_chunks": ingested_count,
            "total_documents": system_docs.count()
        })
        
        return f"Ingested {ingested_count} chunks from {system_docs.count()} documents"
        
    except Exception as e:
        log_error("System documents ingestion failed", exception=e)
        raise e


def extract_text_from_document(document: Document) -> str:
    """Extract text from a document."""
    log_info("Extracting text from document", {
        "filename": document.filename,
        "document_type": document.document_type,
        "file_size": document.file_size
    })
    
    try:
        if document.file.path.endswith('.pdf'):
            import PyPDF2
            with open(document.file.path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                log_success("PDF text extraction completed", {
                    "filename": document.filename,
                    "text_length": len(text.strip()),
                    "page_count": len(pdf_reader.pages)
                })
                return text.strip()
        else:
            # Handle other file types if needed
            with open(document.file.path, 'r', encoding='utf-8') as file:
                text = file.read()
                log_success("Text file extraction completed", {
                    "filename": document.filename,
                    "text_length": len(text)
                })
                return text
    except Exception as e:
        log_error("Text extraction failed", exception=e, extra_data={
            "filename": document.filename,
            "document_type": document.document_type
        })
        return ""

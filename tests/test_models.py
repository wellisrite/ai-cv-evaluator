"""
Unit tests for models.
"""
import uuid
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from evaluation.models import Document, EvaluationJob, EvaluationResult


class DocumentModelTest(TestCase):
    """Test cases for Document model."""
    
    def setUp(self):
        """Set up test data."""
        self.test_file = SimpleUploadedFile(
            "test.pdf", 
            b"fake pdf content", 
            content_type="application/pdf"
        )
        
    def test_document_creation(self):
        """Test document creation."""
        doc = Document.objects.create(
            file=self.test_file,
            document_type='cv',
            filename='test_cv.pdf',
            file_size=1024
        )
        
        self.assertEqual(doc.document_type, 'cv')
        self.assertEqual(doc.filename, 'test_cv.pdf')
        self.assertIsNotNone(doc.id)
        self.assertIsNotNone(doc.uploaded_at)
        
    def test_document_str_representation(self):
        """Test document string representation."""
        doc = Document.objects.create(
            file=self.test_file,
            document_type='project_report',
            filename='test_project.pdf',
            file_size=2048
        )
        
        expected_str = f"Project Report - test_project.pdf"
        self.assertEqual(str(doc), expected_str)
        
    def test_document_choices(self):
        """Test document type choices."""
        # Test valid choices
        doc1 = Document.objects.create(
            file=self.test_file,
            document_type='cv',
            filename='cv.pdf',
            file_size=1024
        )
        doc2 = Document.objects.create(
            file=self.test_file,
            document_type='project_report',
            filename='project.pdf',
            file_size=2048
        )
        
        self.assertEqual(doc1.document_type, 'cv')
        self.assertEqual(doc2.document_type, 'project_report')


class EvaluationJobModelTest(TestCase):
    """Test cases for EvaluationJob model."""
    
    def setUp(self):
        """Set up test data."""
        self.test_file = SimpleUploadedFile(
            "test.pdf", 
            b"fake pdf content", 
            content_type="application/pdf"
        )
        self.cv_doc = Document.objects.create(
            file=self.test_file,
            document_type='cv',
            filename='test_cv.pdf',
            file_size=1024
        )
        self.project_doc = Document.objects.create(
            file=self.test_file,
            document_type='project_report',
            filename='test_project.pdf',
            file_size=2048
        )
        
    def test_evaluation_job_creation(self):
        """Test evaluation job creation."""
        job = EvaluationJob.objects.create(
            job_title='Product Engineer (Backend)',
            cv_document_id=self.cv_doc.id,
            project_document_id=self.project_doc.id
        )
        
        self.assertEqual(job.job_title, 'Product Engineer (Backend)')
        self.assertEqual(job.cv_document_id, self.cv_doc.id)
        self.assertEqual(job.project_document_id, self.project_doc.id)
        self.assertEqual(job.status, 'queued')
        self.assertIsNotNone(job.id)
        self.assertIsNotNone(job.created_at)
        
    def test_evaluation_job_str_representation(self):
        """Test evaluation job string representation."""
        job = EvaluationJob.objects.create(
            job_title='Product Engineer (Backend)',
            cv_document_id=self.cv_doc.id,
            project_document_id=self.project_doc.id
        )
        
        expected_str = f"Evaluation Job {job.id} - Product Engineer (Backend)"
        self.assertEqual(str(job), expected_str)
        
    def test_evaluation_job_status_choices(self):
        """Test evaluation job status choices."""
        job = EvaluationJob.objects.create(
            job_title='Product Engineer (Backend)',
            cv_document_id=self.cv_doc.id,
            project_document_id=self.project_doc.id
        )
        
        # Test status transitions
        self.assertEqual(job.status, 'queued')
        
        job.status = 'processing'
        job.save()
        self.assertEqual(job.status, 'processing')
        
        job.status = 'completed'
        job.save()
        self.assertEqual(job.status, 'completed')
        
        job.status = 'failed'
        job.save()
        self.assertEqual(job.status, 'failed')


class EvaluationResultModelTest(TestCase):
    """Test cases for EvaluationResult model."""
    
    def setUp(self):
        """Set up test data."""
        self.test_file = SimpleUploadedFile(
            "test.pdf", 
            b"fake pdf content", 
            content_type="application/pdf"
        )
        self.cv_doc = Document.objects.create(
            file=self.test_file,
            document_type='cv',
            filename='test_cv.pdf',
            file_size=1024
        )
        self.project_doc = Document.objects.create(
            file=self.test_file,
            document_type='project_report',
            filename='test_project.pdf',
            file_size=2048
        )
        self.job = EvaluationJob.objects.create(
            job_title='Product Engineer (Backend)',
            cv_document_id=self.cv_doc.id,
            project_document_id=self.project_doc.id,
            status='completed'
        )
        
    def test_evaluation_result_creation(self):
        """Test evaluation result creation."""
        result = EvaluationResult.objects.create(
            job=self.job,
            cv_match_rate=0.75,
            cv_feedback='Good candidate',
            project_score=4.2,
            project_feedback='Excellent project',
            overall_summary='Strong candidate overall',
            cv_detailed_scores={'technical_skills_match': {'score': 4, 'reasoning': 'Good'}},
            project_detailed_scores={'correctness': {'score': 5, 'reasoning': 'Excellent'}}
        )
        
        self.assertEqual(result.job, self.job)
        self.assertEqual(result.cv_match_rate, 0.75)
        self.assertEqual(result.cv_feedback, 'Good candidate')
        self.assertEqual(result.project_score, 4.2)
        self.assertEqual(result.project_feedback, 'Excellent project')
        self.assertEqual(result.overall_summary, 'Strong candidate overall')
        self.assertIsNotNone(result.created_at)
        
    def test_evaluation_result_str_representation(self):
        """Test evaluation result string representation."""
        result = EvaluationResult.objects.create(
            job=self.job,
            cv_match_rate=0.75,
            cv_feedback='Good candidate',
            project_score=4.2,
            project_feedback='Excellent project',
            overall_summary='Strong candidate overall',
            cv_detailed_scores={},
            project_detailed_scores={}
        )
        
        expected_str = f"Result for Job {self.job.id}"
        self.assertEqual(str(result), expected_str)
        
    def test_evaluation_result_validation(self):
        """Test evaluation result field validation."""
        # Test valid ranges
        result = EvaluationResult.objects.create(
            job=self.job,
            cv_match_rate=0.0,  # Minimum valid value
            cv_feedback='Test feedback',
            project_score=1.0,  # Minimum valid value
            project_feedback='Test project feedback',
            overall_summary='Test summary',
            cv_detailed_scores={},
            project_detailed_scores={}
        )
        
        self.assertEqual(result.cv_match_rate, 0.0)
        self.assertEqual(result.project_score, 1.0)
        
        # Test maximum valid values
        result.cv_match_rate = 1.0
        result.project_score = 5.0
        result.save()
        
        self.assertEqual(result.cv_match_rate, 1.0)
        self.assertEqual(result.project_score, 5.0)
        
    def test_evaluation_result_json_fields(self):
        """Test evaluation result JSON field handling."""
        cv_scores = {
            'technical_skills_match': {'score': 4, 'reasoning': 'Strong technical background'},
            'experience_level': {'score': 3, 'reasoning': 'Adequate experience'},
            'relevant_achievements': {'score': 4, 'reasoning': 'Good achievements'},
            'cultural_fit': {'score': 3, 'reasoning': 'Good cultural fit'}
        }
        
        project_scores = {
            'correctness': {'score': 5, 'reasoning': 'Perfect implementation'},
            'code_quality': {'score': 4, 'reasoning': 'Good code quality'},
            'resilience': {'score': 4, 'reasoning': 'Good error handling'},
            'documentation': {'score': 3, 'reasoning': 'Adequate documentation'},
            'creativity': {'score': 2, 'reasoning': 'Basic creativity'}
        }
        
        result = EvaluationResult.objects.create(
            job=self.job,
            cv_match_rate=0.75,
            cv_feedback='Good candidate',
            project_score=4.2,
            project_feedback='Excellent project',
            overall_summary='Strong candidate overall',
            cv_detailed_scores=cv_scores,
            project_detailed_scores=project_scores
        )
        
        # Test that JSON fields are properly stored and retrieved
        self.assertEqual(result.cv_detailed_scores, cv_scores)
        self.assertEqual(result.project_detailed_scores, project_scores)
        
        # Test individual score access
        self.assertEqual(result.cv_detailed_scores['technical_skills_match']['score'], 4)
        self.assertEqual(result.project_detailed_scores['correctness']['score'], 5)

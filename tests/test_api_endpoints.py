"""
Unit tests for API endpoints.
"""
import json
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from evaluation.models import Document, EvaluationJob, EvaluationResult


class APITestCase(TestCase):
    """Base test case for API tests."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.cv_file = SimpleUploadedFile(
            "test_cv.pdf", 
            b"fake pdf content", 
            content_type="application/pdf"
        )
        self.project_file = SimpleUploadedFile(
            "test_project.pdf", 
            b"fake project content", 
            content_type="application/pdf"
        )

    def tearDown(self):
        """Clean up test data."""
        # Clean up any uploaded files
        for doc in Document.objects.all():
            if doc.file:
                doc.file.delete()


class UploadEndpointTest(APITestCase):
    """Test cases for document upload endpoint."""
    
    def test_upload_documents_success(self):
        """Test successful document upload."""
        response = self.client.post('/api/upload/', {
            'cv_file': self.cv_file,
            'project_file': self.project_file
        })
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('cv_document_id', data)
        self.assertIn('project_document_id', data)
        self.assertIn('message', data)
        
        # Verify documents were created
        self.assertEqual(Document.objects.count(), 2)
        
    def test_upload_missing_cv_file(self):
        """Test upload with missing CV file."""
        response = self.client.post('/api/upload/', {
            'project_file': self.project_file
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('cv_file', response.json())
        
    def test_upload_missing_project_file(self):
        """Test upload with missing project file."""
        response = self.client.post('/api/upload/', {
            'cv_file': self.cv_file
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('project_file', response.json())
        
    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type."""
        invalid_file = SimpleUploadedFile(
            "test.txt", 
            b"text content", 
            content_type="text/plain"
        )
        
        response = self.client.post('/api/upload/', {
            'cv_file': invalid_file,
            'project_file': self.project_file
        })
        
        self.assertEqual(response.status_code, 400)


class EvaluateEndpointTest(APITestCase):
    """Test cases for evaluation endpoint."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create test documents
        self.cv_doc = Document.objects.create(
            file=self.cv_file,
            document_type='cv',
            filename='test_cv.pdf',
            file_size=1024
        )
        self.project_doc = Document.objects.create(
            file=self.project_file,
            document_type='project_report',
            filename='test_project.pdf',
            file_size=2048
        )
    
    @patch('evaluation.llm_evaluator.LLMEvaluator')
    @patch('evaluation.rag_system_safe.SafeRAGSystem')
    @patch('evaluation.tasks.extract_text_from_document')
    def test_evaluate_documents_success(self, mock_extract, mock_rag, mock_llm):
        """Test successful evaluation request."""
        # Mock the evaluation components
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance
        mock_llm_instance.evaluate_cv.return_value = {
            'technical_skills_match': {'score': 4, 'reasoning': 'Good skills'},
            'experience_level': {'score': 3, 'reasoning': 'Adequate experience'},
            'relevant_achievements': {'score': 4, 'reasoning': 'Good achievements'},
            'cultural_fit': {'score': 3, 'reasoning': 'Good fit'},
            'cv_match_rate': 0.7,
            'cv_feedback': 'Good candidate'
        }
        mock_llm_instance.evaluate_project_report.return_value = {
            'correctness': {'score': 4, 'reasoning': 'Good implementation'},
            'code_quality': {'score': 3, 'reasoning': 'Decent quality'},
            'resilience': {'score': 4, 'reasoning': 'Good error handling'},
            'documentation': {'score': 3, 'reasoning': 'Adequate docs'},
            'creativity': {'score': 2, 'reasoning': 'Basic creativity'},
            'project_score': 3.2,
            'project_feedback': 'Good project'
        }
        mock_llm_instance.generate_overall_summary.return_value = "Good overall candidate"
        
        # Mock text extraction
        mock_extract.return_value = "Sample CV text content"
        
        response = self.client.post('/api/evaluate/', {
            'job_title': 'Product Engineer (Backend)',
            'cv_document_id': str(self.cv_doc.id),
            'project_document_id': str(self.project_doc.id)
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['status'], 'queued')
        
        # Verify job was created
        job = EvaluationJob.objects.get(id=data['id'])
        self.assertEqual(job.job_title, 'Product Engineer (Backend)')
        self.assertEqual(job.cv_document_id, self.cv_doc.id)
        self.assertEqual(job.project_document_id, self.project_doc.id)
        
    def test_evaluate_invalid_document_ids(self):
        """Test evaluation with invalid document IDs."""
        response = self.client.post('/api/evaluate/', {
            'job_title': 'Product Engineer (Backend)',
            'cv_document_id': str(uuid.uuid4()),
            'project_document_id': str(uuid.uuid4())
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
    def test_evaluate_missing_job_title(self):
        """Test evaluation with missing job title."""
        response = self.client.post('/api/evaluate/', {
            'cv_document_id': str(self.cv_doc.id),
            'project_document_id': str(self.project_doc.id)
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 400)


class ResultEndpointTest(APITestCase):
    """Test cases for result endpoint."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.cv_doc = Document.objects.create(
            file=self.cv_file,
            document_type='cv',
            filename='test_cv.pdf',
            file_size=1024
        )
        self.project_doc = Document.objects.create(
            file=self.project_file,
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
        self.result = EvaluationResult.objects.create(
            job=self.job,
            cv_match_rate=0.75,
            cv_feedback='Good candidate',
            project_score=4.2,
            project_feedback='Excellent project',
            overall_summary='Strong candidate overall',
            cv_detailed_scores={'test': 'data'},
            project_detailed_scores={'test': 'data'}
        )
    
    def test_get_result_success(self):
        """Test successful result retrieval."""
        response = self.client.get(f'/api/result/{self.job.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], str(self.job.id))
        self.assertEqual(data['status'], 'completed')
        self.assertIn('result', data)
        
        result_data = data['result']
        self.assertEqual(result_data['cv_match_rate'], 0.75)
        self.assertEqual(result_data['project_score'], 4.2)
        self.assertEqual(result_data['cv_feedback'], 'Good candidate')
        self.assertEqual(result_data['project_feedback'], 'Excellent project')
        self.assertEqual(result_data['overall_summary'], 'Strong candidate overall')
        
    def test_get_result_processing(self):
        """Test result retrieval for processing job."""
        self.job.status = 'processing'
        self.job.save()
        
        response = self.client.get(f'/api/result/{self.job.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'processing')
        self.assertNotIn('result', data)
        
    def test_get_result_not_found(self):
        """Test result retrieval for non-existent job."""
        fake_id = uuid.uuid4()
        response = self.client.get(f'/api/result/{fake_id}/')
        
        self.assertEqual(response.status_code, 404)


class HealthEndpointTest(APITestCase):
    """Test cases for health check endpoint."""
    
    def test_health_check_success(self):
        """Test successful health check."""
        response = self.client.get('/api/health/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('message', data)

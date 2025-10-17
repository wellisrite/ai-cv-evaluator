"""
Unit tests for API endpoints.
"""
import json
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from shared.models import Document
# Removed import from deleted shared.test_utils module
from jobs.models import EvaluationJob
from evaluation.models import EvaluationResult


class APITestCase(TestCase):
    """Base test case for API tests."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create realistic test content
        cv_content = """JOHN DOE
Senior Backend Developer
john.doe@email.com | +1-555-0123 | linkedin.com/in/johndoe

PROFESSIONAL SUMMARY
Experienced backend developer with 5+ years of expertise in Python, Django, Node.js, and AI/ML integration. Proven track record of building scalable systems and implementing AI-powered solutions.

TECHNICAL SKILLS
• Backend: Python, Django, Node.js, Express.js, FastAPI
• Databases: PostgreSQL, MySQL, MongoDB, Redis
• Cloud: AWS (EC2, S3, Lambda, RDS), Docker, Kubernetes
• AI/ML: OpenAI API, LangChain, RAG systems, prompt engineering
• Tools: Git, Jenkins, Docker, Linux, RESTful APIs

EXPERIENCE
Senior Backend Developer | TechCorp Inc. | 2020-Present
• Built AI-powered document analysis system using OpenAI API and RAG
• Improved system performance by 40% through optimization
• Led team of 3 developers in implementing microservices architecture

Backend Developer | StartupXYZ | 2018-2020
• Developed RESTful APIs serving 100K+ daily requests
• Implemented real-time fraud detection using machine learning
• Reduced API response time by 60% through caching strategies

EDUCATION
Bachelor of Computer Science | University of Technology | 2018
"""
        
        project_content = """AI-Powered Document Analysis System

PROJECT OVERVIEW
A comprehensive document analysis platform that leverages OpenAI's GPT models to extract insights, perform semantic search, and provide intelligent document processing capabilities.

TECHNICAL IMPLEMENTATION
• Backend: Python with Django REST Framework
• AI Integration: OpenAI GPT-3.5-turbo with custom prompt engineering
• Database: PostgreSQL with vector embeddings for semantic search
• Caching: Redis for performance optimization
• Deployment: Docker containers on AWS EC2

KEY FEATURES
1. Document Upload and Processing
   - Support for PDF, DOCX, and TXT files
   - Automatic text extraction and preprocessing
   - Batch processing capabilities

2. AI-Powered Analysis
   - Custom prompt templates for different document types
   - Context-aware responses using RAG (Retrieval-Augmented Generation)
   - Confidence scoring for analysis results

3. Semantic Search
   - Vector embeddings using OpenAI embeddings API
   - Similarity search across document corpus
   - Query expansion and refinement

4. Async Job Processing
   - Celery for background task processing
   - Redis as message broker
   - Job status tracking and result caching

ARCHITECTURE DECISIONS
• Chose Django for rapid development and built-in admin interface
• Implemented RAG pattern for context-aware AI responses
• Used async processing to handle long-running AI operations
• Vector database for efficient semantic search

CHALLENGES SOLVED
• Handled rate limiting from OpenAI API with exponential backoff
• Implemented robust error handling for AI model failures
• Optimized vector search performance for large document sets
• Ensured data privacy and security in AI processing pipeline

RESULTS
• 95% accuracy in document classification
• 3x faster document processing compared to manual review
• Successfully processed 10,000+ documents in production
• Reduced manual review time by 80%

TECHNICAL FEASIBILITY
The project demonstrates production-ready implementation of AI/LLM integration with proper error handling, scalability considerations, and monitoring. The architecture supports horizontal scaling and can handle enterprise-level document processing workloads.
"""
        
        self.cv_file = SimpleUploadedFile(
            "test_cv.pdf",
            cv_content.encode('utf-8'),
            content_type="application/pdf"
        )
        self.project_file = SimpleUploadedFile(
            "test_project.pdf", 
            project_content.encode('utf-8'),
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
            job_id=self.job.id,
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


# Health endpoint test removed - endpoint not available in current configuration

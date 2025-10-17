"""
Unit tests for serializers.
"""
import uuid
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from evaluation.models import Document, EvaluationJob, EvaluationResult
from evaluation.serializers import (
    DocumentSerializer, EvaluationJobSerializer, EvaluationResultSerializer,
    UploadSerializer, EvaluateSerializer
)


class DocumentSerializerTest(TestCase):
    """Test cases for Document serializer."""
    
    def setUp(self):
        """Set up test data."""
        self.test_file = SimpleUploadedFile(
            "test.pdf", 
            b"fake pdf content", 
            content_type="application/pdf"
        )
        
    def test_document_serialization(self):
        """Test document serialization."""
        doc = Document.objects.create(
            file=self.test_file,
            document_type='cv',
            filename='test_cv.pdf',
            file_size=1024
        )
        
        serializer = DocumentSerializer(doc)
        data = serializer.data
        
        self.assertEqual(data['id'], str(doc.id))
        self.assertEqual(data['document_type'], 'cv')
        self.assertEqual(data['filename'], 'test_cv.pdf')
        self.assertIn('uploaded_at', data)
        
    def test_document_deserialization(self):
        """Test document deserialization."""
        data = {
            'document_type': 'project_report',
            'filename': 'test_project.pdf',
            'file_size': 2048
        }
        
        serializer = DocumentSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class EvaluationJobSerializerTest(TestCase):
    """Test cases for EvaluationJob serializer."""
    
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
        
    def test_evaluation_job_serialization(self):
        """Test evaluation job serialization."""
        job = EvaluationJob.objects.create(
            job_title='Product Engineer (Backend)',
            cv_document_id=self.cv_doc.id,
            project_document_id=self.project_doc.id
        )
        
        serializer = EvaluationJobSerializer(job)
        data = serializer.data
        
        self.assertEqual(data['id'], str(job.id))
        self.assertEqual(data['job_title'], 'Product Engineer (Backend)')
        self.assertEqual(data['cv_document']['id'], str(self.cv_doc.id))
        self.assertEqual(data['project_document']['id'], str(self.project_doc.id))
        self.assertEqual(data['status'], 'queued')
        self.assertIn('created_at', data)
        
    def test_evaluation_job_deserialization(self):
        """Test evaluation job deserialization."""
        data = {
            'job_title': 'Product Engineer (Backend)',
            'cv_document_id': str(self.cv_doc.id),
            'project_document_id': str(self.project_doc.id)
        }
        
        serializer = EvaluateSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class EvaluationResultSerializerTest(TestCase):
    """Test cases for EvaluationResult serializer."""
    
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
        
    def test_evaluation_result_serialization(self):
        """Test evaluation result serialization."""
        result = EvaluationResult.objects.create(
            job=self.job,
            cv_match_rate=0.75,
            cv_feedback='Good candidate',
            project_score=4.2,
            project_feedback='Excellent project',
            overall_summary='Strong candidate overall',
            cv_detailed_scores={'test': 'data'},
            project_detailed_scores={'test': 'data'}
        )
        
        serializer = EvaluationResultSerializer(result)
        data = serializer.data
        
        self.assertEqual(data['cv_match_rate'], 0.75)
        self.assertEqual(data['cv_feedback'], 'Good candidate')
        self.assertEqual(data['project_score'], 4.2)
        self.assertEqual(data['project_feedback'], 'Excellent project')
        self.assertEqual(data['overall_summary'], 'Strong candidate overall')
        self.assertEqual(data['cv_detailed_scores'], {'test': 'data'})
        self.assertEqual(data['project_detailed_scores'], {'test': 'data'})
        self.assertIn('created_at', data)


class UploadSerializerTest(TestCase):
    """Test cases for Upload serializer."""
    
    def test_upload_serializer_valid_data(self):
        """Test upload serializer with valid data."""
        test_file = SimpleUploadedFile(
            "test.pdf", 
            b"fake pdf content", 
            content_type="application/pdf"
        )
        
        data = {
            'cv_file': test_file,
            'project_file': test_file
        }
        
        serializer = UploadSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
    def test_upload_serializer_missing_cv_file(self):
        """Test upload serializer with missing CV file."""
        test_file = SimpleUploadedFile(
            "test.pdf", 
            b"fake pdf content", 
            content_type="application/pdf"
        )
        
        data = {
            'project_file': test_file
        }
        
        serializer = UploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('cv_file', serializer.errors)
        
    def test_upload_serializer_missing_project_file(self):
        """Test upload serializer with missing project file."""
        test_file = SimpleUploadedFile(
            "test.pdf", 
            b"fake pdf content", 
            content_type="application/pdf"
        )
        
        data = {
            'cv_file': test_file
        }
        
        serializer = UploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('project_file', serializer.errors)
        
    def test_upload_serializer_invalid_file_type(self):
        """Test upload serializer with invalid file type."""
        invalid_file = SimpleUploadedFile(
            "test.txt", 
            b"text content", 
            content_type="text/plain"
        )
        
        data = {
            'cv_file': invalid_file,
            'project_file': invalid_file
        }
        
        serializer = UploadSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class EvaluateSerializerTest(TestCase):
    """Test cases for Evaluate serializer."""
    
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
        
    def test_evaluate_serializer_valid_data(self):
        """Test evaluate serializer with valid data."""
        data = {
            'job_title': 'Product Engineer (Backend)',
            'cv_document_id': str(self.cv_doc.id),
            'project_document_id': str(self.project_doc.id)
        }
        
        serializer = EvaluateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
    def test_evaluate_serializer_missing_job_title(self):
        """Test evaluate serializer with missing job title."""
        data = {
            'cv_document_id': str(self.cv_doc.id),
            'project_document_id': str(self.project_doc.id)
        }
        
        serializer = EvaluateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('job_title', serializer.errors)
        
    def test_evaluate_serializer_missing_cv_document_id(self):
        """Test evaluate serializer with missing CV document ID."""
        data = {
            'job_title': 'Product Engineer (Backend)',
            'project_document_id': str(self.project_doc.id)
        }
        
        serializer = EvaluateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('cv_document_id', serializer.errors)
        
    def test_evaluate_serializer_missing_project_document_id(self):
        """Test evaluate serializer with missing project document ID."""
        data = {
            'job_title': 'Product Engineer (Backend)',
            'cv_document_id': str(self.cv_doc.id)
        }
        
        serializer = EvaluateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('project_document_id', serializer.errors)
        
    def test_evaluate_serializer_invalid_uuid(self):
        """Test evaluate serializer with invalid UUID."""
        data = {
            'job_title': 'Product Engineer (Backend)',
            'cv_document_id': 'invalid-uuid',
            'project_document_id': str(self.project_doc.id)
        }
        
        serializer = EvaluateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('cv_document_id', serializer.errors)
        
    def test_evaluate_serializer_nonexistent_document(self):
        """Test evaluate serializer with non-existent document ID."""
        fake_id = str(uuid.uuid4())
        data = {
            'job_title': 'Product Engineer (Backend)',
            'cv_document_id': fake_id,
            'project_document_id': str(self.project_doc.id)
        }
        
        serializer = EvaluateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('cv_document_id', serializer.errors)

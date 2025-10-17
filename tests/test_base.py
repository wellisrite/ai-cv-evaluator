"""
Base test utilities for all test files.
"""
from django.core.files.uploadedfile import SimpleUploadedFile


class BaseTestCase:
    """Base test case with common utilities."""
    
    def _create_cv_file(self, filename="test_cv.pdf"):
        """Create a realistic CV test file."""
        content = """JOHN DOE
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
        return SimpleUploadedFile(filename, content.encode('utf-8'), content_type="application/pdf")
    
    def _create_project_file(self, filename="test_project.pdf"):
        """Create a realistic project test file."""
        content = """AI-Powered Document Analysis System

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
        return SimpleUploadedFile(filename, content.encode('utf-8'), content_type="application/pdf")

# CV Evaluator - AI-Powered Document Analysis System

A comprehensive Django-based system that leverages OpenAI's GPT models to evaluate CVs and project reports against job requirements. The system uses RAG (Retrieval-Augmented Generation) for context-aware evaluations and Celery for asynchronous processing.

## 🚀 Features

- **AI-Powered CV Evaluation**: Uses OpenAI GPT models to assess candidate CVs against job requirements
- **Project Report Analysis**: Evaluates technical projects with detailed scoring across multiple dimensions
- **Asynchronous Processing**: Celery-based job queue for handling long-running AI evaluations
- **RAG System**: Retrieval-Augmented Generation for context-aware AI responses
- **Vector Database**: ChromaDB for semantic search and document embeddings
- **RESTful API**: Complete API for document upload, evaluation, and result retrieval
- **Real-time Status Tracking**: Monitor evaluation job progress and results
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django API    │    │   Celery Worker │    │   Redis Queue   │
│                 │    │                 │    │                 │
│ • Upload Docs   │───▶│ • Process Jobs  │◀───│ • Job Queue     │
│ • Queue Jobs    │    │ • AI Evaluation │    │ • Results Cache │
│ • Return Results│    │ • Update Status │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Storage  │    │   OpenAI API    │    │   ChromaDB      │
│                 │    │                 │    │                 │
│ • PDF Files     │    │ • GPT-3.5-turbo │    │ • Vector Store  │
│ • Media Files   │    │ • Embeddings    │    │ • Document DB   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
project/
├── src/                          # Django application source code
│   ├── cv_evaluator/            # Main Django project
│   │   ├── settings.py          # Django settings
│   │   ├── urls.py              # Main URL configuration
│   │   ├── celery.py            # Celery configuration
│   │   └── wsgi.py              # WSGI configuration
│   ├── shared/                  # Shared models and utilities
│   │   ├── models.py            # Document model
│   │   ├── views.py             # Upload endpoints
│   │   └── utils.py             # Utility functions
│   ├── evaluation/              # Core evaluation logic
│   │   ├── models.py            # Evaluation models
│   │   ├── views.py             # Evaluation endpoints
│   │   ├── tasks.py             # Celery tasks
│   │   ├── llm_evaluator.py     # OpenAI integration
│   │   ├── rag_system_safe.py   # RAG implementation
│   │   └── serializers.py       # API serializers
│   ├── jobs/                    # Job management
│   │   ├── models.py            # Job models
│   │   └── views.py             # Job endpoints
│   ├── users/                   # User management
│   │   ├── models.py            # User models
│   │   └── views.py             # User endpoints
│   └── manage.py                # Django management script
├── tests/                       # Test suite
│   ├── test_api_endpoints.py    # API endpoint tests
│   ├── test_models.py           # Model tests
│   ├── test_serializers.py      # Serializer tests
│   ├── test_error_handling.py   # Error handling tests
│   └── test_base.py             # Test utilities
├── sample_documents/            # Sample documents for testing
├── media/                       # Uploaded files storage
├── logs/                        # Application logs
├── chroma_db/                   # ChromaDB vector database
├── docker-compose.yml           # Docker Compose configuration
├── Dockerfile                   # Docker image definition
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🛠️ Technology Stack

- **Backend**: Django 4.2.7, Django REST Framework
- **AI/ML**: OpenAI GPT-3.5-turbo, LangChain patterns
- **Task Queue**: Celery 5.3.4 with Redis broker
- **Vector Database**: ChromaDB 0.4.22
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Containerization**: Docker, Docker Compose
- **Testing**: pytest, Django TestCase
- **Document Processing**: PyPDF2 for PDF text extraction

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd project
```

### 2. Environment Setup

Create a `.env` file in the root directory:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Database (optional - defaults to SQLite)
DATABASE_URL=postgresql://user:password@localhost:5432/cv_evaluator

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

### 3. Deploy with Docker

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

This will start:
- **Web server** on http://localhost:8000
- **Redis** on localhost:6379
- **Celery worker** for background processing

### 4. Verify Installation

```bash
# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f web
docker-compose logs -f celery
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Endpoints

#### 1. Upload Documents
```http
POST /api/upload/
Content-Type: multipart/form-data

Form Data:
- cv_file: CV PDF file
- project_file: Project report PDF file
```

**Response:**
```json
{
  "message": "Documents uploaded successfully",
  "cv_document_id": "uuid",
  "project_document_id": "uuid"
}
```

#### 2. Start Evaluation
```http
POST /api/evaluate/
Content-Type: application/json

{
  "job_title": "Product Engineer (Backend)",
  "cv_document_id": "uuid",
  "project_document_id": "uuid"
}
```

**Response:**
```json
{
  "id": "job-uuid",
  "status": "queued",
  "created_at": "2025-01-17T10:00:00Z"
}
```

#### 3. Get Evaluation Result
```http
GET /api/result/{job_id}/
```

**Response:**
```json
{
  "id": "job-uuid",
  "status": "completed",
  "result": {
    "cv_match_rate": 0.77,
    "cv_feedback": "Strong technical skills...",
    "project_score": 4.35,
    "project_feedback": "Excellent implementation...",
    "overall_summary": "Overall assessment...",
    "cv_detailed_scores": {
      "technical_skills_match": {"score": 4, "reasoning": "..."},
      "experience_level": {"score": 4, "reasoning": "..."},
      "relevant_achievements": {"score": 4, "reasoning": "..."},
      "cultural_fit": {"score": 3, "reasoning": "..."}
    },
    "project_detailed_scores": {
      "correctness": {"score": 5, "reasoning": "..."},
      "code_quality": {"score": 4, "reasoning": "..."},
      "resilience": {"score": 4, "reasoning": "..."},
      "documentation": {"score": 5, "reasoning": "..."},
      "creativity": {"score": 4, "reasoning": "..."}
    }
  }
}
```

#### 4. List Jobs
```http
GET /api/jobs/
```

**Response:**
```json
{
  "jobs": [
    {
      "id": "job-uuid",
      "job_title": "Product Engineer (Backend)",
      "status": "completed",
      "created_at": "2025-01-17T10:00:00Z"
    }
  ]
}
```

## 🧪 Testing

### Quick Reference
```bash
# Most common testing commands (using direct docker exec - fastest approach)
docker exec cv-evaluator-web-1 python src/manage.py test --verbosity=2                    # All tests
docker exec cv-evaluator-web-1 python src/manage.py test tests.test_models --verbosity=2   # Model tests
docker exec cv-evaluator-web-1 python src/manage.py test tests.test_api_endpoints --verbosity=2  # API tests
docker exec cv-evaluator-web-1 python src/manage.py test tests.test_serializers --verbosity=2    # Serializer tests
docker exec cv-evaluator-web-1 python src/manage.py test tests.test_error_handling --verbosity=2 # Error handling tests
```

> **💡 Tip**: Using `docker exec cv-evaluator-web-1` is faster than `docker-compose exec web` because it directly executes commands in the running container without going through docker-compose's overhead.

### Run All Tests
```bash
# Using Docker (recommended)
docker exec cv-evaluator-web-1 python src/manage.py test --verbosity=2

# Or using docker-compose
docker-compose exec web python manage.py test --verbosity=2

# Locally (if you have Python environment set up)
cd src
python manage.py test --verbosity=2
```

### Run Specific Test Suites
```bash
# API endpoint tests
docker exec cv-evaluator-web-1 python src/manage.py test tests.test_api_endpoints --verbosity=2

# Model tests
docker exec cv-evaluator-web-1 python src/manage.py test tests.test_models --verbosity=2

# Serializer tests
docker exec cv-evaluator-web-1 python src/manage.py test tests.test_serializers --verbosity=2

# Error handling tests
docker exec cv-evaluator-web-1 python src/manage.py test tests.test_error_handling --verbosity=2

# Run specific test method
docker exec cv-evaluator-web-1 python src/manage.py test tests.test_serializers.EvaluateSerializerTest.test_evaluate_serializer_valid_data --verbosity=2
```

### Run Tests with Coverage
```bash
# Using Docker
docker exec cv-evaluator-web-1 bash -c "cd src && coverage run --source='.' manage.py test"
docker exec cv-evaluator-web-1 bash -c "cd src && coverage report"
docker exec cv-evaluator-web-1 bash -c "cd src && coverage html"  # Generate HTML report

# Copy coverage report to host
docker cp cv-evaluator-web-1:/app/src/htmlcov ./coverage-report
```

### Test with pytest
```bash
# Using Docker
docker exec cv-evaluator-web-1 bash -c "cd src && pytest tests/ -v"

# Or install pytest locally and run
pip install pytest pytest-django
cd src
pytest tests/ -v
```

## 🔧 Development Setup

### Local Development (without Docker)

1. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup Database**
```bash
cd src
python manage.py migrate
python manage.py ingest_documents
```

4. **Start Redis** (required for Celery)
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install Redis locally
# Ubuntu/Debian: sudo apt install redis-server
# macOS: brew install redis
```

5. **Start Celery Worker**
```bash
cd src
celery -A cv_evaluator worker --loglevel=info
```

6. **Start Django Server**
```bash
cd src
python manage.py runserver
```

## 📊 Monitoring and Logging

### View Logs
```bash
# Application logs
tail -f logs/success.log
tail -f logs/error.log

# Docker logs
docker-compose logs -f web
docker-compose logs -f celery
```

### Monitor Celery Tasks
```bash
# Start Celery monitoring
cd src
celery -A cv_evaluator flower
# Access at http://localhost:5555
```

### Database Management
```bash
# Django admin
# Access at http://localhost:8000/admin/

# Create superuser
cd src
python manage.py createsuperuser
```

## 🚀 Production Deployment

### Environment Variables for Production
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgresql://user:password@db-host:5432/cv_evaluator
REDIS_URL=redis://redis-host:6379/0
OPENAI_API_KEY=your-openai-api-key
```

### Docker Production Setup
```bash
# Build production image
docker-compose -f docker-compose.prod.yml up --build

# Or use Docker Swarm/Kubernetes for orchestration
```

### Scaling
- **Horizontal Scaling**: Run multiple Celery workers
- **Database**: Use PostgreSQL with connection pooling
- **Redis**: Use Redis Cluster for high availability
- **Load Balancing**: Use nginx or AWS ALB

## 🔍 Troubleshooting

### Common Issues

1. **Celery Worker Not Processing Jobs**
```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# Restart Celery worker
docker-compose restart celery
```

2. **OpenAI API Errors**
```bash
# Check API key
echo $OPENAI_API_KEY

# Check API quota and billing
# Visit https://platform.openai.com/usage
```

3. **File Upload Issues**
```bash
# Check media directory permissions
ls -la media/

# Check Docker volume mounts
docker-compose exec web ls -la /app/media/
```

4. **Database Migration Issues**
```bash
# Reset migrations (development only)
docker-compose exec web python manage.py migrate --fake-initial
```

### Performance Optimization

1. **Celery Configuration**
```python
# In settings.py
CELERY_TASK_ROUTES = {
    'evaluation.tasks.process_evaluation_job': {'queue': 'evaluation'},
}
```

2. **Database Optimization**
```python
# Use database connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'MAX_CONNS': 20,
        }
    }
}
```

3. **Caching**
```python
# Add Redis caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation
- Use meaningful commit messages
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check this README and inline code comments
- **Logs**: Check `logs/` directory for detailed error information

## 🎯 Roadmap

- [ ] User authentication and authorization
- [ ] Advanced scoring algorithms
- [ ] Batch processing capabilities
- [ ] Real-time notifications
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] API rate limiting
- [ ] Webhook support for external integrations
- [ ] Security for Candidate hidden prompt injection

---

**Built with ❤️ using Django, OpenAI, and modern AI technologies**

# AI-Powered CV Evaluation System

A Django-based backend service that automates the initial screening of job applications using AI and RAG (Retrieval-Augmented Generation) technology. This system is specifically designed for evaluating candidates for the **Product Engineer (Backend)** position at

## 🚀 Features

- **Document Upload**: Upload CV and project report PDFs
- **AI-Powered Evaluation**: Uses OpenAI GPT models for intelligent assessment
- **RAG System**: Retrieval-Augmented Generation for context-aware evaluation
- **Asynchronous Processing**: Non-blocking evaluation pipeline with Celery
- **Comprehensive Scoring**: Multi-criteria evaluation with weighted scoring
- **Error Handling**: Robust retry logic and failure recovery

## 🏗️ Architecture

### Core Components

1. **Django REST API**: Handles file uploads and evaluation requests
2. **Celery Workers**: Process evaluation jobs asynchronously
3. **ChromaDB**: Vector database for document storage and retrieval
4. **OpenAI Integration**: LLM-powered evaluation and analysis
5. **Redis**: Message broker for Celery task queue

### Data Flow

```
Upload Documents → Store in Database → Trigger Evaluation → 
RAG Context Retrieval → LLM Evaluation → Store Results → Return Response
```

## 📋 API Endpoints

### POST /api/upload/
Upload CV and project report documents.

**Request**: `multipart/form-data`
- `cv_file`: PDF file (CV)
- `project_file`: PDF file (Project Report)

**Response**:
```json
{
  "cv_document_id": "uuid",
  "project_document_id": "uuid",
  "message": "Documents uploaded successfully"
}
```

### POST /api/evaluate/
Start evaluation process.

**Request**:
```json
{
  "job_title": "Product Engineer (Backend)",
  "cv_document_id": "uuid",
  "project_document_id": "uuid"
}
```

**Response**:
```json
{
  "id": "job-uuid",
  "status": "queued"
}
```

### GET /api/result/{job_id}/
Get evaluation results.

**Response (Processing)**:
```json
{
  "id": "job-uuid",
  "status": "processing"
}
```

**Response (Completed)**:
```json
{
  "id": "job-uuid",
  "status": "completed",
  "result": {
    "cv_match_rate": 0.82,
    "cv_feedback": "Strong technical background...",
    "project_score": 4.5,
    "project_feedback": "Excellent implementation...",
    "overall_summary": "Good candidate fit...",
    "cv_detailed_scores": {...},
    "project_detailed_scores": {...}
  }
}
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- Redis server
- OpenAI API key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd cv-evaluator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
cp env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: Django secret key
- `REDIS_URL`: Redis connection URL

### 3. Database Setup

```bash
python manage.py migrate
```

### 4. Ingest System Documents

```bash
python manage.py ingest_documents
```

This command will:
- Create system documents (job description, case study brief, rubrics)
- Ingest them into the vector database for RAG retrieval

### 5. Start Services

**Terminal 1 - Django Server**:
```bash
python manage.py runserver
```

**Terminal 2 - Celery Worker**:
```bash
celery -A cv_evaluator worker --loglevel=info
```

**Terminal 3 - Redis Server**:
```bash
redis-server
```

## 🧪 Testing the API

### Using curl

1. **Upload Documents**:
```bash
curl -X POST http://localhost:8000/api/upload/ \
  -F "cv_file=@sample_cv.pdf" \
  -F "project_file=@sample_project.pdf"
```

2. **Start Evaluation**:
```bash
curl -X POST http://localhost:8000/api/evaluate/ \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Product Engineer (Backend)",
    "cv_document_id": "your-cv-uuid",
    "project_document_id": "your-project-uuid"
  }'
```

3. **Check Results**:
```bash
curl http://localhost:8000/api/result/your-job-uuid/
```

### Using Python requests

```python
import requests

# Upload documents
with open('cv.pdf', 'rb') as cv_file, open('project.pdf', 'rb') as project_file:
    files = {'cv_file': cv_file, 'project_file': project_file}
    response = requests.post('http://localhost:8000/api/upload/', files=files)
    data = response.json()
    cv_id = data['cv_document_id']
    project_id = data['project_document_id']

# Start evaluation
eval_data = {
    'job_title': 'Product Engineer (Backend)',
    'cv_document_id': cv_id,
    'project_document_id': project_id
}
response = requests.post('http://localhost:8000/api/evaluate/', json=eval_data)
job_id = response.json()['id']

# Check results
response = requests.get(f'http://localhost:8000/api/result/{job_id}/')
print(response.json())
```

## 📊 Evaluation Criteria

### CV Evaluation (Weighted)
- **Technical Skills Match (40%)**: Alignment with job requirements
- **Experience Level (25%)**: Years of experience and project complexity
- **Relevant Achievements (20%)**: Impact of past work
- **Cultural Fit (15%)**: Communication and learning attitude

### Project Evaluation (Weighted)
- **Correctness (30%)**: Meets requirements (prompt design, chaining, RAG)
- **Code Quality (25%)**: Clean, modular, testable code
- **Resilience (20%)**: Handles failures, retries, error handling
- **Documentation (15%)**: Clear README, setup instructions
- **Creativity (10%)**: Optional improvements and enhancements

## 🔧 Configuration

### LLM Settings
- Model: GPT-3.5-turbo
- Temperature: 0.1 (for consistent results)
- Max tokens: 2000
- Retry logic: 3 attempts with exponential backoff

### Vector Database
- ChromaDB with cosine similarity
- Chunk size: 1000 characters
- Overlap: 200 characters
- Embedding model: text-embedding-ada-002

### File Handling
- Max file size: 10MB
- Supported formats: PDF
- Storage: Django media files

## 🚨 Error Handling

The system includes comprehensive error handling:

- **LLM API Failures**: Retry with exponential backoff
- **File Processing Errors**: Graceful degradation with error messages
- **Vector DB Issues**: Fallback to basic text matching
- **Timeout Handling**: Configurable timeouts for long-running tasks
- **Input Validation**: Sanitization and validation of all inputs

## 📁 Project Structure

```
cv_evaluator/
├── cv_evaluator/          # Django project settings
├── evaluation/            # Main app
│   ├── management/        # Django management commands
│   ├── models.py         # Database models
│   ├── views.py          # API views
│   ├── serializers.py    # API serializers
│   ├── tasks.py          # Celery tasks
│   ├── rag_system.py     # RAG implementation
│   └── llm_evaluator.py  # LLM evaluation logic
├── sample_documents/     # System documents
├── media/               # Uploaded files
├── chroma_db/          # Vector database storage
└── requirements.txt    # Python dependencies
```

## 🔍 Monitoring & Debugging

### Celery Monitoring
```bash
# Monitor Celery tasks
celery -A cv_evaluator flower

# Check task status
celery -A cv_evaluator inspect active
```

### Django Admin
Access `/admin/` to view:
- Uploaded documents
- Evaluation jobs
- Results and scores

### Logs
- Django logs: Console output
- Celery logs: Worker console output
- ChromaDB logs: Vector database operations

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**:
   - Set `DEBUG=False`
   - Use strong `SECRET_KEY`
   - Configure production database

2. **Static Files**:
   ```bash
   python manage.py collectstatic
   ```

3. **Process Management**:
   - Use Gunicorn for Django
   - Use systemd for Celery workers
   - Configure Redis persistence

4. **Security**:
   - Enable HTTPS
   - Configure CORS properly
   - Set up API rate limiting

### Docker Deployment (Optional)

```dockerfile
# Dockerfile example
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "cv_evaluator.wsgi:application"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **ChromaDB/NumPy Compatibility**: The system automatically handles this with fallback mechanisms
2. **OpenAI API Errors**: Check API key validity and account credits
3. **Celery Not Processing**: Ensure Redis is running and Celery worker is started
4. **Database Issues**: Run `python manage.py migrate` to create tables
5. **File Upload Errors**: Check file size limits (10MB max) and PDF format

### Getting Help

- Check the logs for detailed error messages
- Verify all services are running
- Test with sample documents first
- Review the API documentation

## 📈 Performance Optimization

- **Caching**: Implement Redis caching for frequent queries
- **Batch Processing**: Process multiple evaluations in batches
- **Database Optimization**: Add indexes for frequently queried fields
- **CDN**: Use CDN for static file delivery
- **Load Balancing**: Scale with multiple Celery workers

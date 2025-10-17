# Case Study Brief: AI-Powered CV Evaluation System

## Project Overview
Your mission is to build a backend service that automates the initial screening of job applications. The service will receive a candidate's CV and a project report, evaluate them against a specific job description and case study brief, and produce a structured, AI-generated evaluation report.

## Core Requirements

### System Architecture
- **Backend Service**: Implement a robust backend service with RESTful API endpoints
- **Asynchronous Processing**: Handle long-running evaluation tasks without blocking
- **Vector Database**: Use a vector database for document storage and retrieval
- **LLM Integration**: Integrate with AI services for intelligent evaluation

### API Endpoints
1. **POST /upload**: Accept multipart/form-data containing CV and Project Report (PDF)
2. **POST /evaluate**: Trigger asynchronous AI evaluation pipeline
3. **GET /result/{id}**: Retrieve evaluation status and results

### Data Flow
The system operates with clear separation of inputs and reference documents:

#### Candidate-Provided Inputs (To be Evaluated)
- **Candidate CV**: The candidate's resume (PDF)
- **Project Report**: The candidate's project report to our take-home case study (PDF)

#### System-Internal Documents (Ground Truth for Comparison)
- **Job Description**: Document detailing role requirements and responsibilities
- **Case Study Brief**: This document (PDF)
- **Scoring Rubrics**: Predefined evaluation parameters (PDF)

## Technical Implementation Requirements

### RAG (Retrieval-Augmented Generation)
- Ingest all System-Internal Documents into a vector database
- Retrieve relevant sections and inject into prompts
- Implement context-aware document retrieval

### LLM Chaining & Prompt Design
The evaluation pipeline should consist of:

#### CV Evaluation
- Parse candidate's CV into structured data
- Retrieve relevant information from Job Description and CV Scoring Rubrics
- Use LLM to generate: `cv_match_rate` & `cv_feedback`

#### Project Report Evaluation
- Parse candidate's Project Report into structured data
- Retrieve relevant information from Case Study Brief and Project Scoring Rubrics
- Use LLM to generate: `project_score` & `project_feedback`

#### Final Analysis
- Use final LLM call to synthesize outputs into concise `overall_summary`

### Long-Running Process Handling
- POST /evaluate should not block until LLM processing finishes
- Store task, return job ID, allow GET /result/{id} for status checking
- Implement proper job queue management

### Error Handling & Resilience
- Handle LLM API failures (timeouts, rate limits)
- Implement retries with exponential backoff
- Control LLM temperature for stable responses
- Validate and sanitize inputs

## Evaluation Criteria

### CV Evaluation Parameters
1. **Technical Skills Match (40% weight)**: Alignment with job requirements
2. **Experience Level (25% weight)**: Years of experience and project complexity
3. **Relevant Achievements (20% weight)**: Impact of past work
4. **Cultural Fit (15% weight)**: Communication and learning attitude

### Project Deliverable Evaluation
1. **Correctness (30% weight)**: Meets requirements (prompt design, chaining, RAG)
2. **Code Quality (25% weight)**: Clean, modular, testable code
3. **Resilience (20% weight)**: Handles failures, retries, error handling
4. **Documentation (15% weight)**: Clear README, setup instructions
5. **Creativity (10% weight)**: Optional improvements and enhancements

## Expected Output Format

### Evaluation Response Structure
```json
{
  "id": "456",
  "status": "completed",
  "result": {
    "cv_match_rate": 0.82,
    "cv_feedback": "Strong in backend and cloud, limited AI integration experience...",
    "project_score": 4.5,
    "project_feedback": "Meets prompt chaining requirements, lacks error handling robustness...",
    "overall_summary": "Good candidate fit, would benefit from deeper RAG knowledge..."
  }
}
```

## Technical Stack Requirements
- **Backend Framework**: Any modern framework (Django, Rails, Node.js, etc.)
- **LLM Service**: OpenAI, Gemini, or OpenRouter
- **Vector Database**: ChromaDB, Qdrant, or similar
- **Job Queue**: Celery, Sidekiq, or similar for async processing

## Success Criteria
- System successfully processes CV and project report uploads
- AI evaluation provides meaningful and consistent results
- Asynchronous processing works reliably
- Error handling covers common failure scenarios
- Code is clean, well-documented, and maintainable

## Bonus Features (Optional)
- Authentication and authorization
- Deployment configuration
- Monitoring and logging
- Admin dashboard
- API rate limiting
- Caching strategies

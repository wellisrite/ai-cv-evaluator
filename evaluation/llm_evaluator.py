"""
LLM-based evaluation system for CV and project reports.
"""
import json
import time
from typing import Dict, Any, Optional
from openai import OpenAI
from django.conf import settings
from .rag_system_safe import SafeRAGSystem


class LLMEvaluator:
    """Handles LLM-based evaluation of CVs and project reports."""
    
    def __init__(self):
        try:
            # Initialize OpenAI client with minimal configuration
            self.openai_client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=30.0
            )
            print("✅ OpenAI client initialized successfully")
        except Exception as e:
            print(f"⚠️  OpenAI client initialization failed: {e}")
            self.openai_client = None
        self.rag_system = SafeRAGSystem()
    
    def _call_llm_with_retry(self, messages: list, max_retries: int = 3, 
                           temperature: float = 0.1) -> Optional[str]:
        """Call OpenAI API with retry logic."""
        if not self.openai_client:
            print("OpenAI client not available")
            return None
            
        for attempt in range(max_retries):
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"LLM API call failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e
    
    def evaluate_cv(self, cv_text: str, job_title: str) -> Dict[str, Any]:
        """Evaluate CV against job requirements."""
        # Retrieve relevant context
        job_context = self.rag_system.retrieve_relevant_context(
            query=f"job requirements for {job_title}",
            document_types=['job_description', 'cv_rubric'],
            n_results=5
        )
        
        cv_evaluation_prompt = f"""
You are an expert HR professional evaluating a candidate's CV for a {job_title} position.

JOB REQUIREMENTS AND EVALUATION CRITERIA:
{job_context}

CANDIDATE CV:
{cv_text}

Please evaluate the CV based on the following criteria and provide a JSON response with the exact structure below. Pay special attention to AI/LLM experience as this is highly valued for this role:

{{
    "technical_skills_match": {{
        "score": <1-5>,
        "reasoning": "<explanation>"
    }},
    "experience_level": {{
        "score": <1-5>,
        "reasoning": "<explanation>"
    }},
    "relevant_achievements": {{
        "score": <1-5>,
        "reasoning": "<explanation>"
    }},
    "cultural_fit": {{
        "score": <1-5>,
        "reasoning": "<explanation>"
    }},
    "cv_match_rate": <0.0-1.0>,
    "cv_feedback": "<comprehensive feedback in 2-3 sentences>"
}}

Scoring Guidelines:
- Technical Skills Match (40% weight): Alignment with job requirements (backend frameworks like Django/Node.js/Rails, databases, APIs, cloud, AI/LLM integration, prompt design, RAG systems)
- Experience Level (25% weight): Years of experience and project complexity, especially with AI-powered systems
- Relevant Achievements (20% weight): Impact of past work (scaling, performance, adoption, AI/LLM implementations)
- Cultural Fit (15% weight): Communication, learning mindset, teamwork/leadership, "Manager of One" qualities

Calculate cv_match_rate as weighted average: (technical_skills_match * 0.4 + experience_level * 0.25 + relevant_achievements * 0.2 + cultural_fit * 0.15) / 5

Respond ONLY with valid JSON, no additional text.
"""
        
        try:
            response = self._call_llm_with_retry([
                {"role": "system", "content": "You are an expert HR professional. Always respond with valid JSON only."},
                {"role": "user", "content": cv_evaluation_prompt}
            ])
            
            result = json.loads(response)
            return result
        except Exception as e:
            print(f"Error in CV evaluation: {e}")
            return {
                "technical_skills_match": {"score": 1, "reasoning": "Evaluation failed"},
                "experience_level": {"score": 1, "reasoning": "Evaluation failed"},
                "relevant_achievements": {"score": 1, "reasoning": "Evaluation failed"},
                "cultural_fit": {"score": 1, "reasoning": "Evaluation failed"},
                "cv_match_rate": 0.2,
                "cv_feedback": "Unable to evaluate CV due to technical error."
            }
    
    def evaluate_project_report(self, project_text: str) -> Dict[str, Any]:
        """Evaluate project report against case study requirements."""
        # Retrieve relevant context
        project_context = self.rag_system.retrieve_relevant_context(
            query="case study requirements and evaluation criteria",
            document_types=['case_study_brief', 'project_rubric'],
            n_results=5
        )
        
        project_evaluation_prompt = f"""
You are an expert technical reviewer evaluating a project report for a Product Engineer (Backend) position.

CASE STUDY REQUIREMENTS AND EVALUATION CRITERIA:
{project_context}

PROJECT REPORT:
{project_text}

Please evaluate the project report based on the following criteria and provide a JSON response with the exact structure below. Focus on AI/LLM integration capabilities as this is crucial for the role:

{{
    "correctness": {{
        "score": <1-5>,
        "reasoning": "<explanation>"
    }},
    "code_quality": {{
        "score": <1-5>,
        "reasoning": "<explanation>"
    }},
    "resilience": {{
        "score": <1-5>,
        "reasoning": "<explanation>"
    }},
    "documentation": {{
        "score": <1-5>,
        "reasoning": "<explanation>"
    }},
    "creativity": {{
        "score": <1-5>,
        "reasoning": "<explanation>"
    }},
    "project_score": <1.0-5.0>,
    "project_feedback": "<comprehensive feedback in 2-3 sentences>"
}}

Scoring Guidelines:
- Correctness (30% weight): Implements prompt design, LLM chaining (output from one model to another), RAG context injection, async job processing
- Code Quality (25% weight): Clean, modular, reusable, tested code with proper architecture
- Resilience (20% weight): Handles long-running AI processes, retries, randomness/nondeterminism, API failures, job orchestration
- Documentation (15% weight): README clarity, setup instructions, trade-off explanations, technical feasibility insights
- Creativity (10% weight): Extra features beyond requirements, AI-powered enhancements, innovative solutions

Calculate project_score as weighted average: (correctness * 0.3 + code_quality * 0.25 + resilience * 0.2 + documentation * 0.15 + creativity * 0.1)

Respond ONLY with valid JSON, no additional text.
"""
        
        try:
            response = self._call_llm_with_retry([
                {"role": "system", "content": "You are an expert technical reviewer. Always respond with valid JSON only."},
                {"role": "user", "content": project_evaluation_prompt}
            ])
            
            result = json.loads(response)
            return result
        except Exception as e:
            print(f"Error in project evaluation: {e}")
            return {
                "correctness": {"score": 1, "reasoning": "Evaluation failed"},
                "code_quality": {"score": 1, "reasoning": "Evaluation failed"},
                "resilience": {"score": 1, "reasoning": "Evaluation failed"},
                "documentation": {"score": 1, "reasoning": "Evaluation failed"},
                "creativity": {"score": 1, "reasoning": "Evaluation failed"},
                "project_score": 1.0,
                "project_feedback": "Unable to evaluate project report due to technical error."
            }
    
    def generate_overall_summary(self, cv_result: Dict[str, Any], 
                               project_result: Dict[str, Any], 
                               job_title: str) -> str:
        """Generate overall summary combining CV and project evaluations."""
        summary_prompt = f"""
You are an expert HR professional providing a final assessment for a {job_title} candidate.

CV EVALUATION RESULTS:
- Match Rate: {cv_result.get('cv_match_rate', 0):.2f}
- Feedback: {cv_result.get('cv_feedback', 'No feedback available')}

PROJECT EVALUATION RESULTS:
- Score: {project_result.get('project_score', 0):.1f}/5.0
- Feedback: {project_result.get('project_feedback', 'No feedback available')}

Please provide a concise overall summary (3-5 sentences) that includes:
1. Key strengths of the candidate, especially AI/LLM capabilities
2. Areas for improvement or gaps, particularly for AI-powered systems
3. Recommendation for next steps considering "Manager of One" culture

Focus on actionable insights, AI/LLM integration potential, and alignment with values. Be professional and specific to the role requirements.
"""
        
        try:
            response = self._call_llm_with_retry([
                {"role": "system", "content": "You are an expert HR professional providing candidate assessments."},
                {"role": "user", "content": summary_prompt}
            ])
            return response
        except Exception as e:
            print(f"Error generating overall summary: {e}")
            return "Unable to generate overall summary due to technical error."

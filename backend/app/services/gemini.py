import json
import google.generativeai as genai
from app.utils.config import settings
from app.utils.logging import logger
from typing import Dict, Any, List

# Configure the Gemini API client using REST transport to bypass gRPC network limitations
genai.configure(api_key=settings.GEMINI_API_KEY, transport='rest')

class GeminiService:
    @staticmethod
    def _call_gemini_json(prompt: str, model_name: str = "gemini-3.1-flash-lite") -> Dict[str, Any]:
        """Helper to invoke Gemini and enforce a JSON response with automatic rate-limit retries."""
        import time
        max_retries = 3
        backoff_seconds = 5.0
        
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                text_response = response.text.strip()
                
                # Log raw response for diagnostic purposes
                logger.info(f"Gemini API Response length: {len(text_response)} (Attempt {attempt+1})")
                
                # Parse and return JSON
                return json.loads(text_response)
            except Exception as e:
                err_msg = str(e)
                is_rate_limit = "429" in err_msg or "quota" in err_msg.lower() or "resourceexhausted" in err_msg.lower()
                
                if is_rate_limit and attempt < max_retries - 1:
                    logger.warning(
                        f"Gemini API Rate Limit hit (429/Quota). "
                        f"Retrying in {backoff_seconds} seconds... (Attempt {attempt+1}/{max_retries})"
                    )
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2.0  # Exponential backoff
                else:
                    logger.error(f"Error calling Gemini on attempt {attempt+1}: {e}")
                    raise Exception(f"Gemini API evaluation failed: {e}")

    @classmethod
    def parse_resume_text(cls, resume_text: str, spacy_entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """Use Gemini to structure resume text and entities into a standard JSON schema."""
        prompt = f"""
        You are an expert resume parsing system. Analyze the following candidate resume text along with Named Entities extracted by spaCy.
        Extract and structure the information into a single clean JSON object matching the exact specification below. Do not add markdown backticks outside of the JSON representation.

        EXTRACT THE FOLLOWING FIELDS:
        1. name: Candidate's full name (confirm with spaCy entities or text).
        2. email: Candidate's email address.
        3. skills: A list of technical and soft skills mentioned.
        4. experience_years: Estimated total years of experience as a floating number (e.g. 5.5). Look at work dates and summary.
        5. education: A list of objects, each with 'degree', 'institution', and 'year'.
        6. companies: A list of companies the candidate has worked for.
        7. certifications: A list of professional certifications.
        8. projects: A list of projects, each with 'title', 'role', 'description', and 'skills' (associated skills).
        9. achievements: A list of key achievements or awards.

        JSON FORMAT REQUIREMENT:
        {{
            "name": "Full Name",
            "email": "email@example.com",
            "skills": ["Skill1", "Skill2"],
            "experience_years": 4.5,
            "education": [
                {{"degree": "B.S. Computer Science", "institution": "University Name", "year": "2020"}}
            ],
            "companies": ["Company A", "Company B"],
            "certifications": ["Cert A", "Cert B"],
            "projects": [
                {{"title": "Project A", "role": "Lead Developer", "description": "Developed X system using Y", "skills": ["Python", "AWS"]}}
            ],
            "achievements": ["Achievement 1", "Award 2"]
        }}

        ---
        RESUME TEXT:
        {resume_text}

        ---
        SPACY ENTITIES:
        {json.dumps(spacy_entities)}
        """
        try:
            return cls._call_gemini_json(prompt)
        except Exception as e:
            logger.error(f"Fallback parsing for resume text due to: {e}")
            # Return basic schema in case of error
            return {
                "name": spacy_entities.get("PERSON", ["Unknown"])[0] if spacy_entities.get("PERSON") else "Unknown",
                "email": "",
                "skills": [],
                "experience_years": 0.0,
                "education": [],
                "companies": spacy_entities.get("ORG", []),
                "certifications": [],
                "projects": [],
                "achievements": []
            }

    @classmethod
    def parse_job_description(cls, jd_text: str) -> Dict[str, Any]:
        """Extract key components from a Job Description using Gemini."""
        prompt = f"""
        You are a senior recruiter. Analyze the following Job Description (JD).
        Extract key criteria, classify skills, and output a structured JSON.

        FIELDS TO EXTRACT:
        1. role: The title/role of the job.
        2. required_skills: Essential technical or functional skills.
        3. preferred_skills: Nice-to-have or preferred technical/functional skills.
        4. responsibilities: Core responsibilities of the role.
        5. experience_years: Experience requirement (e.g., "5+ years", "Mid-level").
        6. soft_skills: Personality traits or communication skills.
        7. leadership_skills: Leadership indicators requested (e.g. mentoring, management, leading initiatives).
        8. industry: The industry domain (e.g. Fintech, Healthcare, SaaS).
        9. seniority: The seniority tier (e.g. Junior, Mid, Senior, Lead, Principal).
        10. skills_classification: Categorize skills into "mandatory", "preferred", and "nice_to_have".
        11. cleaned_jd: A clean, concise summary text of the core job requirements and tech stack, suitable for text embedding (approx 200-300 words).

        JSON FORMAT REQUIREMENT:
        {{
            "role": "Software Engineer",
            "required_skills": ["Python", "FastAPI"],
            "preferred_skills": ["Docker", "Kubernetes"],
            "responsibilities": ["Build APIs", "Maintain DBs"],
            "experience_years": "3+ years",
            "soft_skills": ["Communication", "Teamwork"],
            "leadership_skills": ["Mentoring"],
            "industry": "Software Engineering",
            "seniority": "Senior",
            "skills_classification": {{
                "mandatory": ["Python", "FastAPI"],
                "preferred": ["Docker"],
                "nice_to_have": ["Kubernetes"]
            }},
            "cleaned_jd": "Concise embedding-ready description of the role."
        }}

        ---
        JOB DESCRIPTION TEXT:
        {jd_text}
        """
        return cls._call_gemini_json(prompt)

    @classmethod
    def evaluate_candidate(cls, anonymized_profile: Dict[str, Any], jd_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate an anonymized candidate profile against a job description's extracted metadata using Gemini."""
        prompt = f"""
        You are a Principal AI Engineer and Senior Architect reviewing a candidate's compatibility for a role.
        Compare the candidate's ANONYMIZED Profile against the Job Description details.

        Rate the candidate across the requested dimensions on a scale of 0 to 100.
        Generate a robust, detailed JSON evaluating their fit.

        FIELDS TO EVALUATE:
        - technical_score: Depth and alignment of technical skills.
        - domain_score: Alignment with the requested industry and domain.
        - leadership: Alignment of leadership skills (mentoring, architecture design, team coordination).
        - growth_score: A score from 0-100 indicating learning speed, project complexity, and career progression speed.
        - semantic_score: Semantic match score of accomplishments to responsibilities.
        - overall_score: Overall calculated match score (should reflect technical, domain, and experience alignment).
        - confidence: Confidence level in this evaluation (0-100%).
        - strengths: A list of key technical or career strengths matching the JD.
        - gaps: List of missing skills or experience gaps.
        - reasoning: 2-3 sentences explaining the assessment reasoning.
        - recommendation: Selection recommendation ("Highly Recommended", "Recommended", "Consider with Gaps", "Not Recommended").

        JSON FORMAT REQUIREMENT:
        {{
            "overall_score": 85.0,
            "semantic_score": 80.0,
            "technical_score": 90.0,
            "domain_score": 85.0,
            "leadership": 75.0,
            "growth_score": 88.0,
            "confidence": 95.0,
            "strengths": ["Strong FastAPI experience", "Background in SaaS"],
            "gaps": ["No experience with Kubernetes"],
            "reasoning": "The candidate has excellent backend engineering skills matching 80% of technical requirements. Domain alignment is high, though they lack container orchestration expertise.",
            "recommendation": "Highly Recommended"
        }}

        ---
        JOB DESCRIPTION (JD) METADATA:
        {json.dumps(jd_metadata)}

        ---
        ANONYMIZED CANDIDATE PROFILE:
        {json.dumps(anonymized_profile)}
        """
        return cls._call_gemini_json(prompt)

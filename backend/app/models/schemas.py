from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

# --- AUTH SCHEMAS ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None

# --- JOB / JD SCHEMAS ---
class JobCreate(BaseModel):
    title: str
    description: str

class JobOut(BaseModel):
    id: str
    recruiter_id: str
    title: str
    description: str
    extracted_metadata: Optional[Dict[str, Any]] = None
    cleaned_jd: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SkillCategory(BaseModel):
    mandatory: List[str] = []
    preferred: List[str] = []
    nice_to_have: List[str] = []

class JDExtractedMetadata(BaseModel):
    role: str
    required_skills: List[str]
    preferred_skills: List[str]
    responsibilities: List[str]
    experience_years: str
    soft_skills: List[str]
    leadership_skills: List[str]
    industry: str
    seniority: str
    skills_classification: SkillCategory

# --- CANDIDATE SCHEMAS ---
class ProjectDetail(BaseModel):
    title: str
    role: str
    description: str
    skills: List[str] = []

class EducationDetail(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None

class ParsedResume(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    skills: List[str] = []
    experience_years: float = 0.0
    education: List[EducationDetail] = []
    companies: List[str] = []
    certifications: List[str] = []
    projects: List[ProjectDetail] = []
    achievements: List[str] = []

class CandidateOut(BaseModel):
    id: str
    recruiter_id: str
    name: str
    email: Optional[str] = None
    resume_url: Optional[str] = None
    original_pdf_path: Optional[str] = None
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# --- EVALUATION AND RANKING SCHEMAS ---
class GrowthScoreDetails(BaseModel):
    growth_score: float
    growth_category: str
    promotion_frequency: float
    skill_expansion: float
    project_complexity: float
    certification_growth: float
    leadership: float
    explanation: str

class CandidateEvaluationOut(BaseModel):
    overall_score: float
    semantic_score: float
    technical_score: float
    domain_score: float
    leadership: float
    growth_score: float
    confidence: float
    strengths: List[str]
    gaps: List[str]
    reasoning: str
    recommendation: str

class RankedCandidateOut(BaseModel):
    rank: int
    candidate_id: str
    name: str
    email: Optional[str] = None
    overall_score: float
    semantic_score: float
    technical_score: float
    domain_score: float
    growth_score: float
    growth_category: str
    recommendation: str
    explainability: Dict[str, Any]
    bias_free_eval: Dict[str, Any]
    full_eval: Dict[str, Any]

class RankingHistoryOut(BaseModel):
    id: str
    job_id: str
    candidate_id: str
    overall_score: float
    semantic_score: float
    technical_score: float
    domain_score: float
    growth_score: float
    explainability: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

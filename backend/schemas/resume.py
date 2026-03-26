"""Resume-related Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ResumeGenerateRequest(BaseModel):
    job_description: str
    existing_resume: Optional[str] = None
    template_id: Optional[int] = None
    additional_context: Optional[str] = None


class ResumeGenerateResponse(BaseModel):
    id: int
    title: str
    content: Dict[str, Any]
    raw_text: str
    ats_score: Optional[float] = None
    keywords_matched: List[str] = []
    keywords_missing: List[str] = []
    version: int


class ResumeAnalyzeRequest(BaseModel):
    resume_text: str
    job_description: Optional[str] = None


class ResumeAnalyzeResponse(BaseModel):
    ats_score: float
    keyword_analysis: Dict[str, Any]
    section_feedback: List[Dict[str, Any]]
    improvement_suggestions: List[str]
    overall_feedback: str


class ResumeListItem(BaseModel):
    id: int
    title: str
    ats_score: Optional[float]
    version: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class CoverLetterRequest(BaseModel):
    company_name: str
    role: str
    job_description: Optional[str] = None
    tone: str = "formal"  # formal, concise, creative
    key_skills: Optional[List[str]] = None
    additional_context: Optional[str] = None


class CoverLetterResponse(BaseModel):
    content: str
    tone: str
    word_count: int

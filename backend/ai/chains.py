"""
LangChain chain definitions for all AI features.
Uses LCEL (LangChain Expression Language) for composable pipelines.
"""
import json
import logging
from typing import Optional, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.ai.model_router import model_router
from backend.ai.prompts import (
    RESUME_GENERATION_PROMPT,
    RESUME_ANALYSIS_PROMPT,
    COVER_LETTER_PROMPT,
    RECRUITER_SIM_PROMPT,
    INTERVIEW_QUESTION_PROMPT,
    INTERVIEW_EVAL_PROMPT,
    SKILL_GAP_PROMPT,
    EMAIL_GENERATION_PROMPT,
    GITHUB_ANALYSIS_PROMPT,
    JD_EXTRACTION_PROMPT,
)
from backend.utils.helpers import clean_ai_response, safe_json_parse

logger = logging.getLogger(__name__)


def _build_chain(prompt_template: str, provider: Optional[str] = None, temperature: float = 0.7):
    """Build a LangChain LCEL chain from a prompt template."""
    prompt = ChatPromptTemplate.from_template(prompt_template)
    llm = model_router.get_llm(provider=provider, temperature=temperature)
    return prompt | llm | StrOutputParser()


def _run_chain(chain, inputs: dict) -> str:
    """Run a chain and handle errors."""
    try:
        result = chain.invoke(inputs)
        return clean_ai_response(result)
    except Exception as e:
        logger.error(f"Chain execution error: {e}")
        raise


def _run_chain_json(chain, inputs: dict) -> dict:
    """Run a chain expecting JSON output."""
    raw = _run_chain(chain, inputs)
    parsed = safe_json_parse(raw)
    if not parsed:
        logger.warning(f"Failed to parse AI JSON response: {raw[:200]}")
        return {"error": "Failed to parse AI response", "raw": raw}
    return parsed


# --- Resume Generation Chain ---
def generate_resume(
    job_description: str,
    existing_resume: str = "",
    additional_context: str = "",
    provider: Optional[str] = None,
) -> dict:
    """Generate ATS-optimized resume content."""
    chain = _build_chain(RESUME_GENERATION_PROMPT, provider=provider, temperature=0.6)
    return _run_chain_json(chain, {
        "job_description": job_description,
        "existing_resume": existing_resume or "Not provided - generate from job description",
        "additional_context": additional_context or "None",
    })


# --- Resume Analysis Chain ---
def analyze_resume(
    resume_text: str,
    job_description: str = "",
    provider: Optional[str] = None,
) -> dict:
    """Analyze resume and provide ATS score + feedback."""
    chain = _build_chain(RESUME_ANALYSIS_PROMPT, provider=provider, temperature=0.3)
    return _run_chain_json(chain, {
        "resume_text": resume_text,
        "job_description": job_description or "No specific job description provided - do a general analysis",
    })


# --- Cover Letter Chain ---
def generate_cover_letter(
    company_name: str,
    role: str,
    job_description: str = "",
    key_skills: str = "",
    tone: str = "formal",
    additional_context: str = "",
    user_profile: str = "",
    provider: Optional[str] = None,
) -> str:
    """Generate personalized cover letter."""
    chain = _build_chain(COVER_LETTER_PROMPT, provider=provider, temperature=0.7)
    return _run_chain(chain, {
        "company_name": company_name,
        "role": role,
        "job_description": job_description or "Not provided",
        "key_skills": key_skills or "Not specified",
        "tone": tone,
        "additional_context": additional_context or "None",
        "user_profile": user_profile or "Not provided",
    })


# --- Recruiter Simulator Chain ---
def simulate_recruiter(
    resume_text: str,
    job_description: str,
    provider: Optional[str] = None,
) -> dict:
    """Simulate recruiter decision on resume."""
    chain = _build_chain(RECRUITER_SIM_PROMPT, provider=provider, temperature=0.4)
    return _run_chain_json(chain, {
        "resume_text": resume_text,
        "job_description": job_description,
    })


# --- Interview Question Generation Chain ---
def generate_interview_questions(
    role: str,
    company: str = "",
    interview_type: str = "mixed",
    difficulty: str = "medium",
    num_questions: int = 5,
    provider: Optional[str] = None,
) -> dict:
    """Generate role-specific interview questions."""
    chain = _build_chain(INTERVIEW_QUESTION_PROMPT, provider=provider, temperature=0.7)
    return _run_chain_json(chain, {
        "role": role,
        "company": company or "a tech company",
        "interview_type": interview_type,
        "difficulty": difficulty,
        "num_questions": str(num_questions),
    })


# --- Interview Evaluation Chain ---
def evaluate_interview_answer(
    question: str,
    answer: str,
    role: str,
    provider: Optional[str] = None,
) -> dict:
    """Evaluate an interview answer."""
    chain = _build_chain(INTERVIEW_EVAL_PROMPT, provider=provider, temperature=0.3)
    return _run_chain_json(chain, {
        "question": question,
        "answer": answer,
        "role": role,
    })


# --- Skill Gap Analysis Chain ---
def analyze_skill_gap(
    job_description: str,
    user_skills: str = "",
    provider: Optional[str] = None,
) -> dict:
    """Analyze skill gaps between user profile and JD."""
    chain = _build_chain(SKILL_GAP_PROMPT, provider=provider, temperature=0.5)
    return _run_chain_json(chain, {
        "job_description": job_description,
        "user_skills": user_skills or "Not provided",
    })


# --- Email Generation Chain ---
def generate_email(
    email_type: str,
    recipient_name: str = "",
    company: str = "",
    role: str = "",
    context: str = "",
    tone: str = "professional",
    provider: Optional[str] = None,
) -> dict:
    """Generate professional emails."""
    chain = _build_chain(EMAIL_GENERATION_PROMPT, provider=provider, temperature=0.7)
    return _run_chain_json(chain, {
        "email_type": email_type,
        "recipient_name": recipient_name or "Hiring Manager",
        "company": company or "the company",
        "role": role or "the position",
        "context": context or "None",
        "tone": tone,
    })


# --- GitHub Analysis Chain ---
def analyze_github_repos(
    repos_data: str,
    provider: Optional[str] = None,
) -> dict:
    """Analyze GitHub repos and generate resume points."""
    chain = _build_chain(GITHUB_ANALYSIS_PROMPT, provider=provider, temperature=0.6)
    return _run_chain_json(chain, {
        "repos_data": repos_data,
    })


# --- JD Extraction Chain ---
def extract_jd_info(
    jd_text: str,
    provider: Optional[str] = None,
) -> dict:
    """Extract structured information from a job description."""
    chain = _build_chain(JD_EXTRACTION_PROMPT, provider=provider, temperature=0.2)
    return _run_chain_json(chain, {
        "jd_text": jd_text,
    })

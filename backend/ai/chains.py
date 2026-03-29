"""
LangChain chain definitions for all AI features.
Uses LCEL (LangChain Expression Language) for composable pipelines.
"""
import time
import logging
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.ai.model_router import model_router
from backend.ai.prompts import (
    RESUME_GENERATION_PROMPT, RESUME_ANALYSIS_PROMPT, COVER_LETTER_PROMPT,
    RECRUITER_SIM_PROMPT, INTERVIEW_QUESTION_PROMPT, INTERVIEW_EVAL_PROMPT,
    SKILL_GAP_PROMPT, EMAIL_GENERATION_PROMPT, GITHUB_ANALYSIS_PROMPT, JD_EXTRACTION_PROMPT,
)
from backend.utils.helpers import clean_ai_response, safe_json_parse

logger = logging.getLogger(__name__)


def _build_chain(
    prompt_template: str,
    provider: Optional[str] = None,
    temperature: float = 0.7,
    # ROOT FIX: Pass max_tokens through so each chain can request the right amount.
    # Previously this was hardcoded to 2000 in model_router.get_llm() default,
    # which caused Gemini to truncate mid-JSON.
    max_tokens: int = 8192,
):
    """Build a LangChain LCEL chain from a prompt template."""
    prompt = ChatPromptTemplate.from_template(prompt_template)
    llm = model_router.get_llm(provider=provider, temperature=temperature, max_tokens=max_tokens)
    return prompt | llm | StrOutputParser()


def _run_chain(
    prompt_template: str,
    inputs: dict,
    provider: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 8192,
) -> str:
    """Run a chain and handle errors with fallback to Ollama."""
    try:
        chain = _build_chain(prompt_template, provider=provider, temperature=temperature, max_tokens=max_tokens)
        result = chain.invoke(inputs)
        return clean_ai_response(result)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Chain execution error: {error_msg}")
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            print("Gemini quota exceeded")
            logger.warning("Gemini quota exceeded")
        
        print("Switching to Ollama...")
        logger.info("Switching to Ollama fallback...")
        try:
            fallback_chain = _build_chain(prompt_template, provider="ollama", temperature=temperature, max_tokens=max_tokens)
            fallback_result = fallback_chain.invoke(inputs)
            return clean_ai_response(fallback_result)
        except Exception as fallback_e:
            logger.error(f"Fallback chain execution error: {fallback_e}")
            raise


def _run_chain_json(
    prompt_template: str,
    inputs: dict,
    provider: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 8192,
) -> dict:
    """Run a chain expecting JSON output with 429 fallback to Ollama (no retries)."""
    try:
        chain = _build_chain(prompt_template, provider=provider, temperature=temperature, max_tokens=max_tokens)
        raw = chain.invoke(inputs)
        raw = clean_ai_response(raw)
        logger.info(f"LLM JSON attempt 1. Raw length: {len(raw)}")

        parsed = safe_json_parse(raw)
        if parsed and "error" not in parsed:
            return parsed

        logger.warning("Failed to parse JSON on primary attempt.")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Primary attempt failed with exception: {error_msg}")
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            print("Gemini quota exceeded")
            logger.warning("Gemini quota exceeded")

    # 🔥 FALLBACK TO OLLAMA
    print("Switching to Ollama...")
    logger.info("Switching to Ollama fallback for JSON...")
    try:
        fallback_chain = _build_chain(prompt_template, provider="ollama", temperature=temperature, max_tokens=max_tokens)
        raw = fallback_chain.invoke(inputs)
        raw = clean_ai_response(raw)
        
        parsed = safe_json_parse(raw)
        if parsed and "error" not in parsed:
            return parsed
            
    except Exception as fallback_e:
        logger.error(f"Ollama fallback JSON execution error: {fallback_e}")

    logger.error("AI execution and fallback failed to produce valid JSON.")
    return {"error": "Failed to parse AI response."}


# --- Resume Generation Chain ---
def generate_resume(
    job_description: str,
    existing_resume: str = "",
    additional_context: str = "",
    provider: Optional[str] = None,
) -> dict:
    return _run_chain_json(
        prompt_template=RESUME_GENERATION_PROMPT,
        inputs={
            "job_description": job_description,
            "existing_resume": existing_resume or "Not provided - generate from job description",
            "additional_context": additional_context or "None",
        },
        provider=provider,
        temperature=0.6,
        max_tokens=8192
    )


# --- Resume Analysis Chain ---
def analyze_resume(
    resume_text: str,
    job_description: str = "",
    provider: Optional[str] = None,
) -> dict:
    return _run_chain_json(
        prompt_template=RESUME_ANALYSIS_PROMPT,
        inputs={
            "resume_text": resume_text,
            "job_description": job_description or "No specific job description provided - do a general analysis",
        },
        provider=provider,
        temperature=0.2,
        max_tokens=4096
    )


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
    return _run_chain(
        prompt_template=COVER_LETTER_PROMPT,
        inputs={
            "company_name": company_name,
            "role": role,
            "job_description": job_description or "Not provided",
            "key_skills": key_skills or "Not specified",
            "tone": tone,
            "additional_context": additional_context or "None",
            "user_profile": user_profile or "Not provided",
        },
        provider=provider,
        temperature=0.7,
        max_tokens=2048
    )


# --- Recruiter Simulator Chain ---
def simulate_recruiter(
    resume_text: str,
    job_description: str,
    provider: Optional[str] = None,
) -> dict:
    return _run_chain_json(
        prompt_template=RECRUITER_SIM_PROMPT,
        inputs={
            "resume_text": resume_text,
            "job_description": job_description,
        },
        provider=provider,
        temperature=0.4,
        max_tokens=4096
    )


# --- Interview Question Generation Chain ---
def generate_interview_questions(
    role: str,
    company: str = "",
    interview_type: str = "mixed",
    difficulty: str = "medium",
    num_questions: int = 5,
    provider: Optional[str] = None,
) -> dict:
    return _run_chain_json(
        prompt_template=INTERVIEW_QUESTION_PROMPT,
        inputs={
            "role": role,
            "company": company or "a tech company",
            "interview_type": interview_type,
            "difficulty": difficulty,
            "num_questions": str(num_questions),
        },
        provider=provider,
        temperature=0.7,
        max_tokens=4096
    )


# --- Interview Evaluation Chain ---
def evaluate_interview_answer(
    question: str,
    answer: str,
    role: str,
    provider: Optional[str] = None,
) -> dict:
    return _run_chain_json(
        prompt_template=INTERVIEW_EVAL_PROMPT,
        inputs={
            "question": question,
            "answer": answer,
            "role": role,
        },
        provider=provider,
        temperature=0.3,
        max_tokens=2048
    )


# --- Skill Gap Analysis Chain ---
def analyze_skill_gap(
    job_description: str,
    user_skills: str = "",
    provider: Optional[str] = None,
) -> dict:
    return _run_chain_json(
        prompt_template=SKILL_GAP_PROMPT,
        inputs={
            "job_description": job_description,
            "user_skills": user_skills or "Not provided",
        },
        provider=provider,
        temperature=0.5,
        max_tokens=4096
    )


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
    return _run_chain_json(
        prompt_template=EMAIL_GENERATION_PROMPT,
        inputs={
            "email_type": email_type,
            "recipient_name": recipient_name or "Hiring Manager",
            "company": company or "the company",
            "role": role or "the position",
            "context": context or "None",
            "tone": tone,
        },
        provider=provider,
        temperature=0.7,
        max_tokens=1024
    )


# --- GitHub Analysis Chain ---
def analyze_github_repos(
    repos_data: str,
    provider: Optional[str] = None,
) -> dict:
    return _run_chain_json(
        prompt_template=GITHUB_ANALYSIS_PROMPT,
        inputs={"repos_data": repos_data},
        provider=provider,
        temperature=0.6,
        max_tokens=4096
    )


# --- JD Extraction Chain ---
def extract_jd_info(
    jd_text: str,
    provider: Optional[str] = None,
) -> dict:
    return _run_chain_json(
        prompt_template=JD_EXTRACTION_PROMPT,
        inputs={"jd_text": jd_text},
        provider=provider,
        temperature=0.2,
        max_tokens=2048
    )

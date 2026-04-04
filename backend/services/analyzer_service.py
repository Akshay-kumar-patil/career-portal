"""Resume analyzer service."""
import logging
from backend.ai.chains import analyze_resume as analyze_resume_chain
from backend.ai.model_router import model_router
from backend.utils.helpers import calculate_keyword_match

logger = logging.getLogger(__name__)


class AnalyzerService:

    def analyze(self, resume_text: str, job_description: str = "") -> dict:
        """
        Full AI-powered resume analysis with ATS scoring.

        - Calls analyze_resume chain (Gemini → auto-falls to Groq on quota error)
        - Validates and sanitizes the response
        - Always appends fast keyword match if JD provided
        - Returns which AI model was actually used
        """
        # Record which provider was active before the call
        # so we can tell the frontend which model ran the analysis
        provider_before = "groq" if model_router._gemini_quota_exhausted else "gemini"

        raw_analysis = analyze_resume_chain(resume_text, job_description)

        # Detect which provider was used after the call
        # (quota flag may have been set during the call)
        provider_used = "groq" if model_router._gemini_quota_exhausted else provider_before

        default_fallback = {
            "ats_score": 0,
            "section_feedback": [],
            "keyword_analysis": {},
            "improvement_suggestions": [],
            "overall_feedback": "Analysis unavailable — AI did not return a valid response.",
            "formatting_issues": [],
            "strengths": [],
            "model_used": provider_used,
            "quota_fallback": model_router._gemini_quota_exhausted,
        }

        # Check for error response from chain
        if not isinstance(raw_analysis, dict):
            logger.warning(f"AI returned non-dict: {type(raw_analysis)}")
            return default_fallback

        if "error" in raw_analysis:
            logger.warning(f"AI chain returned error: {raw_analysis['error']}")
            fallback = default_fallback.copy()
            fallback["overall_feedback"] = f"Analysis failed: {raw_analysis['error']}"
            return fallback

        if "ats_score" not in raw_analysis:
            logger.warning("AI response missing ats_score field")
            return default_fallback

        analysis = raw_analysis

        # Coerce ats_score to int safely
        try:
            analysis["ats_score"] = int(float(analysis.get("ats_score", 0)))
        except (ValueError, TypeError):
            analysis["ats_score"] = 0

        # Ensure all list fields exist and are actually lists
        for key in ["section_feedback", "improvement_suggestions", "formatting_issues", "strengths"]:
            if not isinstance(analysis.get(key), list):
                analysis[key] = []

        # Ensure keyword_analysis is a dict
        if not isinstance(analysis.get("keyword_analysis"), dict):
            analysis["keyword_analysis"] = {}

        # Ensure overall_feedback is a string
        if not isinstance(analysis.get("overall_feedback"), str):
            analysis["overall_feedback"] = ""

        # Stamp which model ran this analysis
        analysis["model_used"] = provider_used
        analysis["quota_fallback"] = model_router._gemini_quota_exhausted

        # Always append fast keyword match if JD provided — free, no AI call needed
        if job_description:
            kw = calculate_keyword_match(resume_text, job_description)
            analysis["keyword_match"] = kw

            # If AI keyword_analysis came back empty, populate from fast match
            if not analysis.get("keyword_analysis"):
                analysis["keyword_analysis"] = {
                    "present_keywords": kw["matched"][:10],
                    "missing_keywords": kw["missing"][:10],
                    "keyword_density_score": int(kw["score"]),
                }

        return analysis

    def quick_score(self, resume_text: str, job_description: str) -> dict:
        """Fast keyword-based scoring — no AI call, instant response."""
        return calculate_keyword_match(resume_text, job_description)


analyzer_service = AnalyzerService()

"""Resume analyzer service."""
from backend.services.ai_service import ai_service
from backend.utils.helpers import calculate_keyword_match


class AnalyzerService:

    def analyze(self, resume_text: str, job_description: str = "") -> dict:
        """Full resume analysis with ATS scoring."""
        # AI-powered analysis
        analysis = ai_service.analyze_resume(resume_text, job_description)

        # Add keyword analysis if JD provided
        if job_description:
            kw = calculate_keyword_match(resume_text, job_description)
            if isinstance(analysis, dict):
                analysis["keyword_match"] = kw

        return analysis

    def quick_score(self, resume_text: str, job_description: str) -> dict:
        """Quick keyword-based scoring without AI."""
        return calculate_keyword_match(resume_text, job_description)


analyzer_service = AnalyzerService()

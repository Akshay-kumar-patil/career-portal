"""
Central AI service — coordinates model routing and chain execution.
"""
from typing import Optional
from backend.ai.model_router import model_router
from backend.ai import chains


class AIService:
    """High-level AI service wrapping all LangChain chains."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider

    def get_status(self) -> dict:
        return model_router.get_status()

    def generate_resume(self, job_description: str, existing_resume: str = "", additional_context: str = "") -> dict:
        return chains.generate_resume(job_description, existing_resume, additional_context, self.provider)

    def analyze_resume(self, resume_text: str, job_description: str = "") -> dict:
        return chains.analyze_resume(resume_text, job_description, self.provider)

    def generate_cover_letter(self, company: str, role: str, jd: str = "", skills: str = "",
                              tone: str = "formal", context: str = "", profile: str = "") -> str:
        return chains.generate_cover_letter(company, role, jd, skills, tone, context, profile, self.provider)

    def simulate_recruiter(self, resume_text: str, job_description: str) -> dict:
        return chains.simulate_recruiter(resume_text, job_description, self.provider)

    def generate_interview_questions(self, role: str, company: str = "", itype: str = "mixed",
                                     difficulty: str = "medium", num: int = 5) -> dict:
        return chains.generate_interview_questions(role, company, itype, difficulty, num, self.provider)

    def evaluate_answer(self, question: str, answer: str, role: str) -> dict:
        return chains.evaluate_interview_answer(question, answer, role, self.provider)

    def analyze_skill_gap(self, jd: str, skills: str = "") -> dict:
        return chains.analyze_skill_gap(jd, skills, self.provider)

    def generate_email(self, email_type: str, recipient: str = "", company: str = "",
                       role: str = "", context: str = "", tone: str = "professional") -> dict:
        return chains.generate_email(email_type, recipient, company, role, context, tone, self.provider)

    def analyze_github(self, repos_data: str) -> dict:
        return chains.analyze_github_repos(repos_data, self.provider)

    def extract_jd(self, jd_text: str) -> dict:
        return chains.extract_jd_info(jd_text, self.provider)

    def smart_rebuild_resume(self, existing_resume: str, github_data: str,
                             job_description: str, additional_context: str = "") -> dict:
        return chains.smart_rebuild_resume(
            existing_resume, github_data, job_description, additional_context, self.provider
        )


# Default instance
ai_service = AIService()

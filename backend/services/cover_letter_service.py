"""Cover letter generation service."""
from backend.services.ai_service import ai_service


class CoverLetterService:

    def generate(self, company: str, role: str, jd: str = "", skills: list = None,
                 tone: str = "formal", context: str = "", profile: str = "") -> dict:
        """Generate a personalized cover letter."""
        skills_str = ", ".join(skills) if skills else ""
        content = ai_service.generate_cover_letter(company, role, jd, skills_str, tone, context, profile)
        word_count = len(content.split()) if isinstance(content, str) else 0
        return {
            "content": content,
            "tone": tone,
            "word_count": word_count,
        }


cover_letter_service = CoverLetterService()

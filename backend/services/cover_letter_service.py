"""Cover letter generation service."""
from backend.services.ai_service import ai_service


class CoverLetterService:

    def generate(self, company: str, role: str, jd: str = "", skills: list = None,
                 tone: str = "formal", context: str = "", profile: str = "") -> dict:
        """Generate a personalized cover letter."""
        skills_str = ", ".join(skills) if skills else ""
        content = ai_service.generate_cover_letter(company, role, jd, skills_str, tone, context, profile)
        
        word_count = 0
        if isinstance(content, dict):
            paragraphs = content.get("body_paragraphs", [])
            word_count = sum(len(str(p).split()) for p in paragraphs)
            
            # Incorporate profile details automatically
            import json
            try:
                prof = json.loads(profile)
                content["user_name"] = prof.get("full_name", "")
                contact = prof.get("contact", {})
                content["user_location"] = contact.get("location", "")
                content["user_phone"] = contact.get("phone", "")
                content["user_email"] = contact.get("email", "")
            except:
                pass
        elif isinstance(content, str):
            word_count = len(content.split())
            
        return {
            "content": content,
            "tone": tone,
            "word_count": word_count,
        }


cover_letter_service = CoverLetterService()

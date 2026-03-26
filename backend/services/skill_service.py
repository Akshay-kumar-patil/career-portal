"""Skill gap analysis service."""
from backend.services.ai_service import ai_service


class SkillService:

    def analyze_gap(self, job_description: str, user_skills: list = None) -> dict:
        skills_str = ", ".join(user_skills) if user_skills else ""
        return ai_service.analyze_skill_gap(job_description, skills_str)


skill_service = SkillService()

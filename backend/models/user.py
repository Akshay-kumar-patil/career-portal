"""User model for authentication and profile storage."""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_username = Column(String(100), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    skills = Column(Text, default="[]")  # JSON array
    experience_years = Column(Integer, default=0)
    current_role = Column(String(255), nullable=True)
    target_role = Column(String(255), nullable=True)
    education = Column(Text, default="[]")  # JSON array
    work_experience = Column(Text, default="[]")  # JSON array
    projects = Column(Text, default="[]")  # JSON array
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_skills_list(self):
        return json.loads(self.skills) if self.skills else []

    def set_skills_list(self, skills_list):
        self.skills = json.dumps(skills_list)

    def get_profile_dict(self):
        """Return full profile as dictionary for AI context."""
        return {
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "linkedin_url": self.linkedin_url,
            "github_username": self.github_username,
            "portfolio_url": self.portfolio_url,
            "skills": self.get_skills_list(),
            "experience_years": self.experience_years,
            "current_role": self.current_role,
            "target_role": self.target_role,
            "education": json.loads(self.education) if self.education else [],
            "work_experience": json.loads(self.work_experience) if self.work_experience else [],
            "projects": json.loads(self.projects) if self.projects else [],
            "summary": self.summary,
        }

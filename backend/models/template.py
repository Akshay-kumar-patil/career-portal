"""Template and InterviewSession models."""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from backend.database import Base


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # resume, cover_letter
    description = Column(Text, nullable=True)
    html_content = Column(Text, nullable=False)
    preview_image = Column(String(500), nullable=True)
    is_default = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    interview_type = Column(String(50), default="mixed")  # hr, technical, mixed
    questions = Column(Text, default="[]")  # JSON array
    answers = Column(Text, default="[]")  # JSON array
    scores = Column(Text, default="[]")  # JSON array
    overall_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def get_questions_list(self):
        return json.loads(self.questions) if self.questions else []

    def get_scores_list(self):
        return json.loads(self.scores) if self.scores else []

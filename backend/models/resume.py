"""Resume and ResumeVersion models."""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # JSON: structured resume content
    raw_text = Column(Text, nullable=True)  # Plain text version
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    ats_score = Column(Float, nullable=True)
    target_jd = Column(Text, nullable=True)  # Target job description
    keywords_matched = Column(Text, default="[]")  # JSON array
    keywords_missing = Column(Text, default="[]")  # JSON array
    version = Column(Integer, default=1)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship("ResumeVersion", back_populates="resume")

    def get_content_dict(self):
        return json.loads(self.content) if self.content else {}

    def set_content_dict(self, content_dict):
        self.content = json.dumps(content_dict)


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)  # JSON snapshot
    change_summary = Column(Text, nullable=True)
    ats_score = Column(Float, nullable=True)
    performance_metrics = Column(Text, default="{}")  # JSON: views, callbacks, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="versions")

    def get_metrics(self):
        return json.loads(self.performance_metrics) if self.performance_metrics else {}

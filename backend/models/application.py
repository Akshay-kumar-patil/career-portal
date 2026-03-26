"""Job Application tracking model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Enum
import enum
from backend.database import Base


class ApplicationStatus(str, enum.Enum):
    SAVED = "saved"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    TECHNICAL = "technical"
    FINAL_ROUND = "final_round"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    status = Column(String(50), default=ApplicationStatus.SAVED.value)
    applied_date = Column(DateTime, nullable=True)
    jd_text = Column(Text, nullable=True)
    jd_url = Column(String(500), nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    cover_letter_used = Column(Integer, default=0)
    salary_range = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    job_type = Column(String(50), nullable=True)  # remote, hybrid, onsite
    source = Column(String(100), nullable=True)  # linkedin, indeed, referral, etc.
    referral_id = Column(Integer, ForeignKey("referrals.id"), nullable=True)
    notes = Column(Text, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    response_date = Column(DateTime, nullable=True)
    interview_date = Column(DateTime, nullable=True)
    excitement_level = Column(Integer, default=3)  # 1-5 scale
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

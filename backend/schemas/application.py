"""Application and Referral Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ApplicationCreate(BaseModel):
    company: str
    role: str
    status: str = "saved"
    jd_text: Optional[str] = None
    jd_url: Optional[str] = None
    resume_id: Optional[int] = None
    salary_range: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    source: Optional[str] = None
    referral_id: Optional[int] = None
    notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    excitement_level: int = 3


class ApplicationUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    response_date: Optional[datetime] = None
    excitement_level: Optional[int] = None


class ApplicationResponse(BaseModel):
    id: int
    company: str
    role: str
    status: str
    applied_date: Optional[datetime]
    location: Optional[str]
    job_type: Optional[str]
    source: Optional[str]
    salary_range: Optional[str]
    notes: Optional[str]
    follow_up_date: Optional[datetime]
    interview_date: Optional[datetime]
    excitement_level: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReferralCreate(BaseModel):
    contact_name: str
    company: str
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    relationship: Optional[str] = None
    notes: Optional[str] = None


class ReferralUpdate(BaseModel):
    contact_name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None


class ReferralResponse(BaseModel):
    id: int
    contact_name: str
    company: str
    role: Optional[str]
    email: Optional[str]
    linkedin_url: Optional[str]
    relationship: Optional[str]
    status: str
    notes: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

"""User-related Pydantic schemas — MongoDB-compatible (id is a string)."""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    education: Optional[List[dict]] = None
    work_experience: Optional[List[dict]] = None
    projects: Optional[List[dict]] = None
    summary: Optional[str] = None


class UserResponse(BaseModel):
    id: str                             # MongoDB ObjectId serialised to string
    email: str
    full_name: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: Optional[List[str]] = []
    experience_years: int = 0
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    education: Optional[List[dict]] = []
    work_experience: Optional[List[dict]] = []
    projects: Optional[List[dict]] = []
    summary: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

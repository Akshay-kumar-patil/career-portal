"""Skill gap analysis API routes."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas.ai import SkillGapRequest, SkillGapResponse
from backend.utils.auth import get_current_user
from backend.services.skill_service import skill_service

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.post("/analyze-gap")
def analyze_gap(req: SkillGapRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        skills = req.user_skills
        if not skills:
            raw_skills = current_user.get("skills", [])
            skills = raw_skills if isinstance(raw_skills, list) else []
        result = skill_service.analyze_gap(req.job_description, skills)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

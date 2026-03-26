"""Skill gap analysis API routes."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.schemas.ai import SkillGapRequest, SkillGapResponse
from backend.utils.auth import get_current_user
from backend.services.skill_service import skill_service

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.post("/analyze-gap")
def analyze_gap(req: SkillGapRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        skills = req.user_skills
        if not skills:
            skills = json.loads(current_user.skills) if current_user.skills else []
        result = skill_service.analyze_gap(req.job_description, skills)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

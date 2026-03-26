"""Cover letter generation API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.schemas.resume import CoverLetterRequest, CoverLetterResponse
from backend.utils.auth import get_current_user
from backend.services.cover_letter_service import cover_letter_service
from backend.services.memory_service import memory_service

router = APIRouter(prefix="/api/cover-letter", tags=["Cover Letter"])


@router.post("/generate", response_model=CoverLetterResponse)
def generate_cover_letter(
    req: CoverLetterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        profile = memory_service.get_user_context(db, current_user.id)
        result = cover_letter_service.generate(
            company=req.company_name,
            role=req.role,
            jd=req.job_description or "",
            skills=req.key_skills,
            tone=req.tone,
            context=req.additional_context or "",
            profile=profile,
        )
        return CoverLetterResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

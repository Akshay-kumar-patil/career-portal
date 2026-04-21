"""Referral management API routes."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.referral import Referral
from backend.schemas.application import ReferralCreate, ReferralUpdate, ReferralResponse
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/api/referrals", tags=["Referrals"])


@router.post("/", response_model=ReferralResponse)
def create_referral(req: ReferralCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = Referral(user_id=current_user["id"], **req.model_dump())
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return ref


@router.get("/", response_model=list[ReferralResponse])
def list_referrals(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Referral).filter(Referral.user_id == current_user["id"]).order_by(Referral.created_at.desc()).all()


@router.put("/{ref_id}", response_model=ReferralResponse)
def update_referral(ref_id: int, req: ReferralUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = db.query(Referral).filter(Referral.id == ref_id, Referral.user_id == current_user["id"]).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Referral not found")
    for key, value in req.model_dump(exclude_none=True).items():
        setattr(ref, key, value)
    db.commit()
    db.refresh(ref)
    return ref


@router.delete("/{ref_id}")
def delete_referral(ref_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = db.query(Referral).filter(Referral.id == ref_id, Referral.user_id == current_user["id"]).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Referral not found")
    db.delete(ref)
    db.commit()
    return {"message": "Referral deleted"}

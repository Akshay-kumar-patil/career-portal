"""Job application tracking API routes."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.application import Application
from backend.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/api/applications", tags=["Applications"])


@router.post("/", response_model=ApplicationResponse)
def create_application(req: ApplicationCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    app = Application(user_id=current_user["id"], **req.model_dump())
    if req.status != "saved":
        app.applied_date = datetime.utcnow()
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.get("/", response_model=list[ApplicationResponse])
def list_applications(
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Application).filter(Application.user_id == current_user["id"])
    if status:
        query = query.filter(Application.status == status)
    return query.order_by(Application.created_at.desc()).all()


@router.get("/{app_id}", response_model=ApplicationResponse)
def get_application(app_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user["id"]).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.put("/{app_id}", response_model=ApplicationResponse)
def update_application(app_id: int, req: ApplicationUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user["id"]).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    updates = req.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(app, key, value)
    if "status" in updates and updates["status"] == "applied" and not app.applied_date:
        app.applied_date = datetime.utcnow()
    db.commit()
    db.refresh(app)
    return app


@router.delete("/{app_id}")
def delete_application(app_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user["id"]).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(app)
    db.commit()
    return {"message": "Application deleted"}

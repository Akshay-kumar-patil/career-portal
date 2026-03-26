"""Authentication API routes."""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.schemas.user import UserRegister, UserLogin, UserProfile, UserResponse, TokenResponse
from backend.utils.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id, email=user.email, full_name=user.full_name,
            created_at=user.created_at,
        ),
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id, email=user.email, full_name=user.full_name,
            skills=json.loads(user.skills) if user.skills else [],
            experience_years=user.experience_years or 0,
            current_role=user.current_role,
            target_role=user.target_role,
            created_at=user.created_at,
        ),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        skills=json.loads(current_user.skills) if current_user.skills else [],
        experience_years=current_user.experience_years or 0,
        current_role=current_user.current_role,
        target_role=current_user.target_role,
        created_at=current_user.created_at,
    )


@router.put("/profile")
def update_profile(data: UserProfile, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    updates = data.model_dump(exclude_none=True)
    for key, value in updates.items():
        if key in ("skills", "education", "work_experience", "projects"):
            setattr(current_user, key, json.dumps(value) if isinstance(value, (list, dict)) else value)
        else:
            setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated", "user_id": current_user.id}

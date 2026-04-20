"""Authentication API routes — supports email/password and Google OAuth.

Flow for Google OAuth:
  1.  Frontend opens  GET /api/auth/google  in a new browser tab.
  2.  Backend redirects the browser to Google's consent screen.
  3.  Google redirects to  GET /api/auth/google/callback  with a one-time code.
  4.  Backend exchanges the code for an ID-token, creates/finds the SQLite user,
      syncs to MongoDB, generates a JWT, then redirects to the Streamlit frontend
      with the token in the query-param ?auth_token=<jwt>.
  5.  Streamlit's existing session-restore logic picks up auth_token automatically.
"""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db, get_users_collection
from backend.models.user import User
from backend.schemas.user import UserRegister, UserLogin, UserProfile, UserResponse, TokenResponse
from backend.utils.auth import (
    hash_password, verify_password, create_access_token, get_current_user,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# ─── Google OAuth client (authlib) ─────────────────────────────────────────
_oauth = None


def _get_oauth():
    """Lazily create the OAuth client so missing credentials don't crash startup."""
    global _oauth
    if _oauth is not None:
        return _oauth
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return None
    try:
        from authlib.integrations.starlette_client import OAuth
        oauth = OAuth()
        oauth.register(
            name="google",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
        _oauth = oauth
        return _oauth
    except Exception as exc:
        logger.warning("Google OAuth not available: %s", exc)
        return None


# ─── MongoDB helper ─────────────────────────────────────────────────────────
def _sync_user_to_mongo(user: User, provider: str = "local") -> None:
    """Mirror a SQLite user record into MongoDB career.users collection."""
    try:
        col = get_users_collection()
        if col is None:
            return
        doc = {
            "sqlite_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "auth_provider": provider,
            "phone": user.phone,
            "linkedin_url": user.linkedin_url,
            "github_username": user.github_username,
            "portfolio_url": user.portfolio_url,
            "skills": user.skills or [],
            "experience_years": user.experience_years or 0,
            "current_role": user.current_role,
            "target_role": user.target_role,
            "created_at": user.created_at or datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        col.update_one({"email": user.email}, {"$set": doc}, upsert=True)
        logger.debug("User %s synced to MongoDB (provider=%s)", user.email, provider)
    except Exception as exc:
        # MongoDB sync failure must never break the auth flow
        logger.warning("MongoDB sync failed for %s: %s", user.email, exc)


# ─── Standard Email / Password Routes ───────────────────────────────────────

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

    _sync_user_to_mongo(user, provider="local")

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
    if not user or not verify_password(data.password, user.hashed_password or ""):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    _sync_user_to_mongo(user, provider="local")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id, email=user.email, full_name=user.full_name,
            skills=user.skills or [],
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
        skills=current_user.skills or [],
        experience_years=current_user.experience_years or 0,
        current_role=current_user.current_role,
        target_role=current_user.target_role,
        created_at=current_user.created_at,
    )


@router.put("/profile")
def update_profile(
    data: UserProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updates = data.model_dump(exclude_none=True)
    for key, value in updates.items():
        if key in ("skills", "education", "work_experience", "projects"):
            setattr(current_user, key, json.dumps(value) if isinstance(value, (list, dict)) else value)
        else:
            setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    _sync_user_to_mongo(current_user, provider="local")
    return {"message": "Profile updated", "user_id": current_user.id}


# ─── Google OAuth Routes ─────────────────────────────────────────────────────

@router.get("/google")
async def google_login(request: Request):
    """Redirect the browser to Google's consent screen."""
    oauth = _get_oauth()
    if oauth is None:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle the OAuth callback from Google, issue a JWT, redirect to frontend."""
    oauth = _get_oauth()
    if oauth is None:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured.")

    try:
        token_data = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        logger.error("Google OAuth token exchange failed: %s", exc)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?oauth_error=token_exchange_failed",
            status_code=302,
        )

    user_info = token_data.get("userinfo") or {}
    email = user_info.get("email")
    full_name = user_info.get("name", email)
    google_id = user_info.get("sub")

    if not email:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?oauth_error=no_email",
            status_code=302,
        )

    # Find or create the user in SQLite
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password="",           # Google users have no local password
            full_name=full_name or email,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("New user created via Google OAuth: %s", email)
    else:
        # Update name in case it changed on Google side
        if full_name and user.full_name != full_name:
            user.full_name = full_name
            db.commit()
            db.refresh(user)

    _sync_user_to_mongo(user, provider="google")

    jwt_token = create_access_token({"sub": str(user.id)})

    # Redirect back to Streamlit — existing _restore_from_query_params() will
    # pick up auth_token automatically and log the user in without extra code.
    redirect_url = f"{settings.FRONTEND_URL}/?auth_token={jwt_token}"
    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("/google/status")
def google_oauth_status():
    """Check whether Google OAuth is configured on this server."""
    configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    return {
        "configured": configured,
        "login_url": "/api/auth/google" if configured else None,
        "hint": (
            "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env to enable Google login."
            if not configured else None
        ),
    }

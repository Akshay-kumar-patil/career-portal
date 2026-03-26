"""Personal memory service — stores and retrieves user context for AI."""
import json
from sqlalchemy.orm import Session
from backend.models.user import User
from backend.models.resume import Resume
from backend.models.application import Application


class MemoryService:

    def get_user_context(self, db: Session, user_id: int) -> str:
        """Assemble full user context for AI prompts."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return "No user profile found."

        profile = user.get_profile_dict()

        # Get latest resume
        latest_resume = db.query(Resume).filter(
            Resume.user_id == user_id, Resume.is_active == 1
        ).order_by(Resume.created_at.desc()).first()

        # Get application stats
        apps = db.query(Application).filter(Application.user_id == user_id).all()
        app_stats = {
            "total": len(apps),
            "by_status": {},
        }
        for app in apps:
            status = app.status
            app_stats["by_status"][status] = app_stats["by_status"].get(status, 0) + 1

        context_parts = [
            f"User Profile: {json.dumps(profile)}",
            f"Application History: {json.dumps(app_stats)}",
        ]

        if latest_resume:
            context_parts.append(f"Latest Resume (v{latest_resume.version}): {latest_resume.raw_text[:1000]}")

        return "\n\n".join(context_parts)

    def update_profile(self, db: Session, user_id: int, updates: dict) -> User:
        """Update user profile fields."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        for key, value in updates.items():
            if hasattr(user, key):
                if key in ("skills", "education", "work_experience", "projects"):
                    setattr(user, key, json.dumps(value) if isinstance(value, (list, dict)) else value)
                else:
                    setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user


memory_service = MemoryService()

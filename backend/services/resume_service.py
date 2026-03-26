"""Resume generation and management service."""
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.models.resume import Resume, ResumeVersion
from backend.services.ai_service import ai_service
from backend.ai.embeddings import store_resume_embedding
from backend.utils.helpers import calculate_keyword_match


class ResumeService:

    def generate(self, db: Session, user_id: int, job_description: str,
                 existing_resume: str = "", template_id: Optional[int] = None,
                 additional_context: str = "") -> Resume:
        """Generate a new ATS-optimized resume."""
        # Generate via AI
        content = ai_service.generate_resume(job_description, existing_resume, additional_context)

        # Calculate keyword match
        raw_text = json.dumps(content, indent=2) if isinstance(content, dict) else str(content)
        kw_analysis = calculate_keyword_match(raw_text, job_description)

        # Extract title
        role = content.get("summary", "")[:60] if isinstance(content, dict) else "Generated Resume"
        title = f"Resume - {role}" if role else "Generated Resume"

        # Save to DB
        resume = Resume(
            user_id=user_id,
            title=title,
            content=json.dumps(content),
            raw_text=raw_text,
            template_id=template_id,
            ats_score=kw_analysis["score"],
            target_jd=job_description,
            keywords_matched=json.dumps(kw_analysis["matched"]),
            keywords_missing=json.dumps(kw_analysis["missing"]),
            version=1,
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # Save initial version
        version = ResumeVersion(
            resume_id=resume.id,
            version_number=1,
            content=json.dumps(content),
            change_summary="Initial generation",
            ats_score=kw_analysis["score"],
        )
        db.add(version)
        db.commit()

        # Store embedding for semantic search
        store_resume_embedding(
            str(resume.id), raw_text,
            {"user_id": str(user_id), "title": title}
        )

        return resume

    def get_by_id(self, db: Session, resume_id: int, user_id: int) -> Optional[Resume]:
        return db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()

    def list_user_resumes(self, db: Session, user_id: int) -> List[Resume]:
        return db.query(Resume).filter(Resume.user_id == user_id, Resume.is_active == 1).order_by(Resume.created_at.desc()).all()

    def get_versions(self, db: Session, resume_id: int) -> List[ResumeVersion]:
        return db.query(ResumeVersion).filter(ResumeVersion.resume_id == resume_id).order_by(ResumeVersion.version_number.desc()).all()

    def delete(self, db: Session, resume_id: int, user_id: int) -> bool:
        resume = self.get_by_id(db, resume_id, user_id)
        if resume:
            resume.is_active = 0
            db.commit()
            return True
        return False


resume_service = ResumeService()

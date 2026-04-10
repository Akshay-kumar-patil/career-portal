"""Resume generation and management service."""
import json
import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.resume import Resume, ResumeVersion
from backend.services.ai_service import ai_service
from backend.ai.embeddings import store_resume_embedding
from backend.utils.helpers import calculate_keyword_match

logger = logging.getLogger(__name__)


class ResumeService:

    def generate(self, db: Session, user_id: int, job_description: str,
                 existing_resume: str = "", template_id: Optional[int] = None,
                 additional_context: str = "") -> Resume:
        """Generate a new ATS-optimized resume with comprehensive error handling."""
        start_time = datetime.now()
        print(f"\n[SERVICE] Starting resume generation for user_id: {user_id}...")
        print(f"[SERVICE] JD Length: {len(job_description)} chars | Existing Data: {len(existing_resume)} chars")
        
        try:
            # Generate via AI
            # Use specialized smart rebuild if GitHub data is detected in the input
            if "=== GITHUB PROFILE DATA ===" in existing_resume:
                parts = existing_resume.split("=== GITHUB PROFILE DATA ===")
                resume_part = parts[0].replace("=== EXISTING RESUME (extracted text) ===", "").strip()
                github_part = parts[1].strip()
                content = ai_service.smart_rebuild_resume(resume_part, github_part, job_description, additional_context)
            else:
                content = ai_service.generate_resume(job_description, existing_resume, additional_context)
            
            # Check for AI errors
            if isinstance(content, dict) and "error" in content:
                err_msg = content.get("error", "Unknown AI error")
                error_type = content.get("error_type", "unknown")
                logger.error(
                    f"AI generation failed: {err_msg}",
                    extra={
                        "user_id": user_id,
                        "error_type": error_type,
                        "jd_length": len(job_description)
                    }
                )
                raise RuntimeError(f"AI failed to generate resume: {err_msg}")

            # Validate JSON structure
            if not isinstance(content, dict):
                logger.error(
                    f"Invalid AI response type: {type(content)}",
                    extra={
                        "user_id": user_id,
                        "response_preview": str(content)[:200] if content else "None"
                    }
                )
                raise ValueError("AI returned non-JSON response")

            # Check required fields
            required_fields = ["full_name", "contact", "summary", "education", "experience"]
            missing_fields = [f for f in required_fields if f not in content or not content[f]]
            
            if missing_fields:
                logger.warning(
                    f"Missing fields in AI response: {missing_fields}",
                    extra={"user_id": user_id, "missing": missing_fields}
                )

            print(f"[SERVICE] AI data received for {content.get('full_name', 'User')}")

            # Calculate keyword match
            raw_text = json.dumps(content, indent=2) if isinstance(content, dict) else str(content)
            kw_analysis = calculate_keyword_match(raw_text, job_description)
            print(f"[ATS] Match Analysis: {kw_analysis['total_matched']} keywords found. Score: {kw_analysis['score']}%")

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
            
            # Log success metrics
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Resume generated successfully",
                extra={
                    "resume_id": resume.id,
                    "user_id": user_id,
                    "ats_score": kw_analysis["score"],
                    "keywords_matched": len(kw_analysis["matched"]),
                    "keywords_missing": len(kw_analysis["missing"]),
                    "elapsed_seconds": elapsed
                }
            )
            print(f"[DB] Saved resume ID: {resume.id}")

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
            try:
                store_resume_embedding(
                    str(resume.id), raw_text,
                    {"user_id": str(user_id), "title": title}
                )
                logger.debug(f"Embedding stored successfully for resume {resume.id}")
                print("[SEMANTIC] Embedding stored successfully.")
            except Exception as e:
                logger.warning(
                    f"Could not store embedding",
                    extra={
                        "resume_id": resume.id,
                        "error": str(e)
                    }
                )
                print(f"[WARNING] Could not store embedding: {e}")

            return resume

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Resume generation failed",
                extra={
                    "user_id": user_id,
                    "error": str(e),
                    "jd_length": len(job_description),
                    "existing_resume_length": len(existing_resume),
                    "elapsed_seconds": elapsed
                },
                exc_info=True
            )
            raise

    def get_by_id(self, db: Session, resume_id: int, user_id: int) -> Optional[Resume]:
        """Fetch resume by ID with user validation."""
        try:
            resume = db.query(Resume).filter(
                Resume.id == resume_id,
                Resume.user_id == user_id
            ).first()
            
            if resume:
                logger.debug(f"Retrieved resume {resume_id} for user {user_id}")
            else:
                logger.warning(f"Resume {resume_id} not found for user {user_id}")
            
            return resume
        except Exception as e:
            logger.error(f"Error fetching resume {resume_id}: {e}")
            return None

    def list_user_resumes(self, db: Session, user_id: int) -> List[Resume]:
        """List active resumes for user, ordered by creation date."""
        try:
            resumes = db.query(Resume).filter(
                Resume.user_id == user_id,
                Resume.is_active == 1
            ).order_by(Resume.created_at.desc()).all()
            
            logger.debug(f"Listed {len(resumes)} resumes for user {user_id}")
            return resumes
        except Exception as e:
            logger.error(f"Error listing resumes for user {user_id}: {e}")
            return []

    def get_versions(self, db: Session, resume_id: int) -> List[ResumeVersion]:
        """Get version history for a resume."""
        try:
            versions = db.query(ResumeVersion).filter(
                ResumeVersion.resume_id == resume_id
            ).order_by(ResumeVersion.version_number.desc()).all()
            
            logger.debug(f"Retrieved {len(versions)} versions for resume {resume_id}")
            return versions
        except Exception as e:
            logger.error(f"Error fetching versions for resume {resume_id}: {e}")
            return []

    def delete(self, db: Session, resume_id: int, user_id: int) -> bool:
        """Soft delete resume (marks as inactive)."""
        try:
            resume = self.get_by_id(db, resume_id, user_id)
            if resume:
                resume.is_active = 0
                db.commit()
                logger.info(f"Resume {resume_id} deleted (soft delete) for user {user_id}")
                return True
            else:
                logger.warning(f"Resume {resume_id} not found for user {user_id} - cannot delete")
                return False
        except Exception as e:
            logger.error(f"Error deleting resume {resume_id}: {e}")
            return False


resume_service = ResumeService()

"""Scheduled cleanup service for generated files and old resumes."""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple
from sqlalchemy.orm import Session
from backend.config import settings
from backend.models.resume import Resume

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for cleaning up old files and inactive resumes."""
    
    @staticmethod
    def cleanup_old_generated_files() -> Tuple[int, int]:
        """
        Delete generated files older than FILE_RETENTION_DAYS.
        
        Returns:
            Tuple of (deleted_count, error_count)
        """
        try:
            generated_dir = Path(settings.GENERATED_DIR)
            if not generated_dir.exists():
                logger.warning(f"Generated directory does not exist: {settings.GENERATED_DIR}")
                return 0, 0
            
            cutoff_time = datetime.now() - timedelta(days=settings.FILE_RETENTION_DAYS)
            cutoff_timestamp = cutoff_time.timestamp()
            
            deleted_count = 0
            error_count = 0
            
            logger.info(
                f"Starting cleanup of files older than {settings.FILE_RETENTION_DAYS} days",
                extra={"cutoff_date": cutoff_time.isoformat()}
            )
            
            for filepath in generated_dir.glob("*"):
                if filepath.is_file():
                    try:
                        file_mtime = filepath.stat().st_mtime
                        if file_mtime < cutoff_timestamp:
                            file_size = filepath.stat().st_size
                            filepath.unlink()
                            deleted_count += 1
                            
                            logger.debug(
                                f"Deleted old generated file",
                                extra={
                                    "file": filepath.name,
                                    "file_size": file_size,
                                    "age_days": (datetime.now() - datetime.fromtimestamp(file_mtime)).days
                                }
                            )
                    except Exception as e:
                        error_count += 1
                        logger.warning(
                            f"Failed to delete file",
                            extra={"file": filepath.name, "error": str(e)}
                        )
            
            logger.info(
                f"File cleanup completed",
                extra={
                    "deleted": deleted_count,
                    "errors": error_count,
                    "directory": settings.GENERATED_DIR
                }
            )
            
            return deleted_count, error_count
        
        except Exception as e:
            logger.error(f"Cleanup error: {e}", exc_info=True)
            return 0, 1
    
    @staticmethod
    def cleanup_inactive_resumes(db: Session, days: int = None) -> Tuple[int, int]:
        """
        Soft-delete resumes that have been inactive for N days.
        
        Args:
            db: Database session
            days: Number of days of inactivity before cleanup (uses config if not specified)
        
        Returns:
            Tuple of (cleaned_count, error_count)
        """
        try:
            if days is None:
                days = settings.RESUME_RETENTION_DAYS
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            logger.info(
                f"Starting cleanup of inactive resumes (>={days} days inactive)",
                extra={"cutoff_date": cutoff_date.isoformat()}
            )
            
            # Find inactive resumes that haven't been updated
            inactive_resumes = db.query(Resume).filter(
                Resume.is_active == 1,
                Resume.updated_at < cutoff_date if hasattr(Resume, 'updated_at') else Resume.created_at < cutoff_date
            ).all()
            
            cleaned_count = 0
            error_count = 0
            
            for resume in inactive_resumes:
                try:
                    resume.is_active = 0
                    db.commit()
                    cleaned_count += 1
                    
                    logger.debug(
                        f"Marked resume as inactive",
                        extra={
                            "resume_id": resume.id,
                            "user_id": resume.user_id,
                            "days_inactive": days
                        }
                    )
                except Exception as e:
                    error_count += 1
                    db.rollback()
                    logger.warning(
                        f"Failed to clean resume",
                        extra={"resume_id": resume.id, "error": str(e)}
                    )
            
            logger.info(
                f"Resume cleanup completed",
                extra={
                    "cleaned": cleaned_count,
                    "errors": error_count,
                    "retention_days": days
                }
            )
            
            return cleaned_count, error_count
        
        except Exception as e:
            logger.error(f"Resume cleanup error: {e}", exc_info=True)
            return 0, 1
    
    @staticmethod
    def full_cleanup(db: Session) -> dict:
        """
        Run full cleanup: files + inactive resumes.
        
        Args:
            db: Database session
        
        Returns:
            Dictionary with cleanup statistics
        """
        logger.info("Starting full cleanup cycle")
        
        # Clean files
        files_deleted, files_errors = CleanupService.cleanup_old_generated_files()
        
        # Clean resumes
        resumes_cleaned, resumes_errors = CleanupService.cleanup_inactive_resumes(db)
        
        result = {
            "files_deleted": files_deleted,
            "files_errors": files_errors,
            "resumes_cleaned": resumes_cleaned,
            "resumes_errors": resumes_errors,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(
            f"Full cleanup cycle completed",
            extra=result
        )
        
        return result


cleanup_service = CleanupService()

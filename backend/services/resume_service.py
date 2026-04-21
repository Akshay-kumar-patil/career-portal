"""Resume generation and management service — MongoDB primary."""
import json
import logging
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from backend.database import get_resumes_collection
from backend.services.ai_service import ai_service
from backend.ai.embeddings import store_resume_embedding
from backend.utils.helpers import calculate_keyword_match

logger = logging.getLogger(__name__)


def _resume_doc_to_dict(doc: dict) -> dict:
    """Convert a MongoDB resume document to a serialisable dict."""
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    # Ensure content is a dict (stored as dict in Mongo, no need to json.loads)
    if isinstance(doc.get("content"), str):
        try:
            doc["content"] = json.loads(doc["content"])
        except (TypeError, ValueError):
            doc["content"] = {}
    return doc


class ResumeService:

    def generate(
        self,
        user_id: str,
        job_description: str,
        existing_resume: str = "",
        template_id: Optional[str] = None,
        additional_context: str = "",
    ) -> dict:
        """Generate a new ATS-optimised resume and store it in MongoDB."""
        start_time = datetime.utcnow()
        print(f"\n[SERVICE] Starting resume generation for user_id: {user_id}...")
        print(f"[SERVICE] JD Length: {len(job_description)} chars | Existing Data: {len(existing_resume)} chars")

        try:
            # ── AI generation ──────────────────────────────────────────────────
            if "=== GITHUB PROFILE DATA ===" in existing_resume:
                parts = existing_resume.split("=== GITHUB PROFILE DATA ===")
                resume_part = parts[0].replace("=== EXISTING RESUME (extracted text) ===", "").strip()
                github_part = parts[1].strip()
                content = ai_service.smart_rebuild_resume(resume_part, github_part, job_description, additional_context)
            else:
                content = ai_service.generate_resume(job_description, existing_resume, additional_context)

            if isinstance(content, dict) and "error" in content:
                raise RuntimeError(f"AI failed to generate resume: {content.get('error', 'Unknown AI error')}")

            if not isinstance(content, dict):
                raise ValueError("AI returned non-JSON response")

            required_fields = ["full_name", "contact", "summary", "education", "experience"]
            missing = [f for f in required_fields if f not in content or not content[f]]
            if missing:
                logger.warning("Missing fields in AI response: %s for user %s", missing, user_id)

            print(f"[SERVICE] AI data received for {content.get('full_name', 'User')}")

            # ── Keyword / ATS scoring ──────────────────────────────────────────
            raw_text = json.dumps(content, indent=2)
            kw_analysis = calculate_keyword_match(raw_text, job_description)
            print(f"[ATS] Score: {kw_analysis['score']}% | Matched: {kw_analysis['total_matched']} keywords")

            role = content.get("summary", "")[:60] or "Generated Resume"
            title = f"Resume - {role}"

            # ── Persist to MongoDB ─────────────────────────────────────────────
            now = datetime.utcnow()
            resume_doc = {
                "user_id": user_id,            # string ObjectId of the user
                "title": title,
                "content": content,            # stored as dict — no JSON encoding needed
                "raw_text": raw_text,
                "template_id": str(template_id) if template_id else None,
                "ats_score": kw_analysis["score"],
                "target_jd": job_description,
                "keywords_matched": kw_analysis["matched"],
                "keywords_missing": kw_analysis["missing"],
                "version": 1,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }

            col = get_resumes_collection()
            result = col.insert_one(resume_doc)
            resume_doc["_id"] = result.inserted_id
            resume_doc["id"] = str(result.inserted_id)

            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                "Resume generated: id=%s user=%s ats=%.1f elapsed=%.2fs",
                resume_doc["id"], user_id, kw_analysis["score"], elapsed,
            )
            print(f"[DB] Saved resume ID: {resume_doc['id']}")

            # ── Store version snapshot ─────────────────────────────────────────
            version_doc = {
                "resume_id": resume_doc["id"],
                "version_number": 1,
                "content": content,
                "change_summary": "Initial generation",
                "ats_score": kw_analysis["score"],
                "created_at": now,
            }
            col.database["resume_versions"].insert_one(version_doc)

            # ── Semantic embedding ─────────────────────────────────────────────
            try:
                store_resume_embedding(
                    resume_doc["id"], raw_text,
                    {"user_id": user_id, "title": title},
                )
                print("[SEMANTIC] Embedding stored successfully.")
            except Exception as emb_err:
                logger.warning("Could not store embedding for resume %s: %s", resume_doc["id"], emb_err)
                print(f"[WARNING] Could not store embedding: {emb_err}")

            return resume_doc

        except Exception:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                "Resume generation failed for user %s after %.2fs",
                user_id, elapsed, exc_info=True,
            )
            raise

    def get_by_id(self, resume_id: str, user_id: str) -> Optional[dict]:
        """Fetch a resume by ID, ensuring it belongs to user_id."""
        try:
            col = get_resumes_collection()
            doc = col.find_one({"_id": ObjectId(resume_id), "user_id": user_id})
            return _resume_doc_to_dict(doc)
        except Exception as e:
            logger.error("Error fetching resume %s: %s", resume_id, e)
            return None

    def list_user_resumes(self, user_id: str) -> List[dict]:
        """List active resumes for a user, newest first."""
        try:
            col = get_resumes_collection()
            docs = col.find(
                {"user_id": user_id, "is_active": True},
                sort=[("created_at", -1)],
            )
            return [_resume_doc_to_dict(d) for d in docs]
        except Exception as e:
            logger.error("Error listing resumes for user %s: %s", user_id, e)
            return []

    def get_versions(self, resume_id: str) -> List[dict]:
        """Get version history for a resume."""
        try:
            col = get_resumes_collection()
            docs = col.database["resume_versions"].find(
                {"resume_id": resume_id},
                sort=[("version_number", -1)],
            )
            results = []
            for d in docs:
                d["id"] = str(d.pop("_id"))
                results.append(d)
            return results
        except Exception as e:
            logger.error("Error fetching versions for resume %s: %s", resume_id, e)
            return []

    def delete(self, resume_id: str, user_id: str) -> bool:
        """Soft-delete a resume (mark is_active=False)."""
        try:
            col = get_resumes_collection()
            result = col.update_one(
                {"_id": ObjectId(resume_id), "user_id": user_id},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}},
            )
            if result.matched_count:
                logger.info("Resume %s soft-deleted for user %s", resume_id, user_id)
                return True
            logger.warning("Resume %s not found for user %s", resume_id, user_id)
            return False
        except Exception as e:
            logger.error("Error deleting resume %s: %s", resume_id, e)
            return False


resume_service = ResumeService()

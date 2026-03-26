"""Extraction service for PDFs, DOCX, URLs, and JD parsing."""
from backend.services.ai_service import ai_service
from backend.utils.pdf_parser import extract_text_from_file, extract_text_from_url
from backend.ai.embeddings import store_jd_embedding
import uuid


class ExtractionService:

    def extract_from_file(self, file_bytes: bytes, filename: str) -> str:
        return extract_text_from_file(file_bytes, filename)

    def extract_from_url(self, url: str) -> str:
        return extract_text_from_url(url) or ""

    def parse_jd(self, text: str = None, url: str = None) -> dict:
        """Extract structured info from JD text or URL."""
        if url and not text:
            text = self.extract_from_url(url)
        if not text:
            return {"error": "No text provided"}

        result = ai_service.extract_jd(text)

        # Store embedding for future matching
        jd_id = str(uuid.uuid4())
        store_jd_embedding(jd_id, text, {
            "company": result.get("company", ""),
            "role": result.get("role", ""),
        })

        return result


extraction_service = ExtractionService()

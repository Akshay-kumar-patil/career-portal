"""PDF and DOCX parsing utilities."""
import io
from typing import Optional


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text content from a PDF file."""
    try:
        # FIX: pypdf replaces deprecated PyPDF2 (no security updates since 2022)
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = [page.extract_text() for page in reader.pages if page.extract_text()]
        return "\n".join(text_parts)
    except ImportError:
        # Graceful fallback if pypdf not yet installed
        try:
            from PyPDF2 import PdfReader  # type: ignore
            reader = PdfReader(io.BytesIO(file_bytes))
            text_parts = [p.extract_text() for p in reader.pages if p.extract_text()]
            return "\n".join(text_parts)
        except Exception as e:
            return f"Error extracting PDF text: {str(e)}"
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text content from a DOCX file."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(text_parts)
    except Exception as e:
        return f"Error extracting DOCX text: {str(e)}"


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Auto-detect file type and extract text."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file_bytes)
    else:
        return file_bytes.decode("utf-8", errors="ignore")


def extract_text_from_url(url: str) -> Optional[str]:
    """Extract main text content from a URL."""
    try:
        import requests
        from bs4 import BeautifulSoup
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for el in soup(["script", "style", "nav", "footer", "header"]):
            el.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        return f"Error extracting URL text: {str(e)}"

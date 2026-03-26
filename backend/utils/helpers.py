"""General helper utilities."""
import json
from datetime import datetime
from typing import Any


def safe_json_parse(text: str, default: Any = None) -> Any:
    """Safely parse JSON string, return default on failure."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}


def format_date(dt: datetime) -> str:
    """Format datetime to human-readable string."""
    if dt is None:
        return "N/A"
    return dt.strftime("%b %d, %Y")


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length with ellipsis."""
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length] + "..."


def clean_ai_response(response: str) -> str:
    """Clean AI response by removing markdown code blocks if present."""
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    elif response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    return response.strip()


def calculate_keyword_match(resume_text: str, jd_text: str) -> dict:
    """Calculate keyword overlap between resume and JD."""
    import re

    def extract_keywords(text: str) -> set:
        # Simple keyword extraction: words 3+ chars, lowered
        words = re.findall(r'\b[a-zA-Z+#]{3,}\b', text.lower())
        # Filter common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'had', 'her', 'was', 'one', 'our', 'out', 'has', 'have', 'from',
            'they', 'been', 'this', 'that', 'with', 'will', 'each', 'make',
            'like', 'just', 'over', 'such', 'take', 'than', 'them', 'very',
            'some', 'could', 'would', 'about', 'which', 'their', 'other',
            'experience', 'work', 'working', 'ability', 'strong', 'team',
            'role', 'position', 'looking', 'join', 'company',
        }
        return {w for w in words if w not in stop_words}

    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd_text)

    matched = resume_keywords & jd_keywords
    missing = jd_keywords - resume_keywords

    score = (len(matched) / max(len(jd_keywords), 1)) * 100

    return {
        "matched": sorted(list(matched))[:50],
        "missing": sorted(list(missing))[:30],
        "score": round(score, 1),
        "total_jd_keywords": len(jd_keywords),
        "total_matched": len(matched),
    }

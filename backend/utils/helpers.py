"""General helper utilities."""
import json
import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def fix_truncated_json(text: str) -> str:
    """
    Heuristically auto-close truncated JSON.
    Handles the exact error case where Gemini cuts output mid-string,
    e.g. '{"feedback": "Comprehensive contact details including profe'
    """
    text = text.strip()
    in_string = False
    escape = False
    open_brackets = []

    for char in text:
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
        elif char == '"':
            in_string = not in_string
        elif not in_string:
            if char == "{":
                open_brackets.append("{")
            elif char == "[":
                open_brackets.append("[")
            elif char == "}":
                if open_brackets and open_brackets[-1] == "{":
                    open_brackets.pop()
            elif char == "]":
                if open_brackets and open_brackets[-1] == "[":
                    open_brackets.pop()

    # Close any open string first
    if in_string:
        text += '"'

    # Remove trailing comma before we close brackets (common in truncated output)
    text = re.sub(r",\s*$", "", text.rstrip())

    # Close open brackets in reverse order
    for bracket in reversed(open_brackets):
        if bracket == "{":
            text += "}"
        elif bracket == "[":
            text += "]"

    return text


def safe_json_parse(text: str, default: Any = None) -> Any:
    """
    Safely parse JSON with multi-stage truncation recovery.

    Stage 1: Direct parse (fast path — works when output is clean)
    Stage 2: Strip markdown fences and retry
    Stage 3: Extract JSON block by finding outermost { } or [ ]
    Stage 4: Heuristic truncation recovery via fix_truncated_json()

    This handles the Gemini truncation bug where output is cut mid-string.
    """
    if not text:
        return default if default is not None else {}

    # Stage 1: direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Stage 2: strip markdown fences
    cleaned = text
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0]
    elif "```" in cleaned:
        cleaned = cleaned.replace("```", "")
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        pass

    # Stage 3: extract first JSON block
    try:
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(cleaned[start:end])
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start != -1 and end > start:
            return json.loads(cleaned[start:end])
    except (json.JSONDecodeError, TypeError):
        pass

    # Stage 4: truncation recovery — this is the Gemini fix
    try:
        start = cleaned.find("{")
        if start != -1:
            recovered = fix_truncated_json(cleaned[start:])
            result = json.loads(recovered)
            logger.warning("JSON was truncated and recovered via fix_truncated_json()")
            return result
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"JSON truncation recovery failed: {e}")

    logger.error(f"Complete JSON parse failure. Input preview (500 chars): {text[:500]}")
    return default if default is not None else {}


def load_json_field(value: Any, default: Any = None) -> Any:
    """
    Safely load a model field that may be a JSON string or already a Python object.
    Use this for legacy Text columns. For new JSON columns, the value is already native.
    """
    if value is None:
        return default if default is not None else []
    if isinstance(value, (list, dict)):
        return value
    return safe_json_parse(value, default)


def format_date(dt: datetime) -> str:
    if dt is None:
        return "N/A"
    return dt.strftime("%b %d, %Y")


def truncate_text(text: str, max_length: int = 500) -> str:
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length] + "..."


def clean_ai_response(response: str) -> str:
    """Strip markdown code fences from AI response."""
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
    def extract_keywords(text: str) -> set:
        words = re.findall(r"\b[a-zA-Z+#]{3,}\b", text.lower())
        stop_words = {
            "the", "and", "for", "are", "but", "not", "you", "all", "can",
            "had", "her", "was", "one", "our", "out", "has", "have", "from",
            "they", "been", "this", "that", "with", "will", "each", "make",
            "like", "just", "over", "such", "take", "than", "them", "very",
            "some", "could", "would", "about", "which", "their", "other",
            "experience", "work", "working", "ability", "strong", "team",
            "role", "position", "looking", "join", "company",
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

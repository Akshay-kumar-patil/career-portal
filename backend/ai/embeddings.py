"""
Embedding pipeline for semantic search using ChromaDB.
Uses HuggingFace sentence-transformers (works fully offline).
"""
import logging
from typing import List, Optional, Dict, Any
from backend.database import get_chroma_collection
from backend.config import settings

logger = logging.getLogger(__name__)

# Lazy-loaded embedding model
_embedding_model = None


def get_embedding_model():
    """Lazy-load the sentence-transformer model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}. Semantic search unavailable.")
            return None
    return _embedding_model


def generate_embeddings(texts: List[str]) -> Optional[List[List[float]]]:
    """Generate embeddings for a list of texts."""
    model = get_embedding_model()
    if model is None:
        return None
    try:
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        return None


def store_resume_embedding(
    resume_id: str,
    resume_text: str,
    metadata: Dict[str, Any] = None,
) -> bool:
    """Store a resume embedding in ChromaDB."""
    embeddings = generate_embeddings([resume_text])
    if embeddings is None:
        return False
    try:
        collection = get_chroma_collection("resumes")
        collection.upsert(
            ids=[str(resume_id)],
            embeddings=embeddings,
            documents=[resume_text],
            metadatas=[metadata or {}],
        )
        return True
    except Exception as e:
        logger.error(f"Failed to store resume embedding: {e}")
        return False


def store_jd_embedding(
    jd_id: str,
    jd_text: str,
    metadata: Dict[str, Any] = None,
) -> bool:
    """Store a job description embedding in ChromaDB."""
    embeddings = generate_embeddings([jd_text])
    if embeddings is None:
        return False
    try:
        collection = get_chroma_collection("job_descriptions")
        collection.upsert(
            ids=[str(jd_id)],
            embeddings=embeddings,
            documents=[jd_text],
            metadatas=[metadata or {}],
        )
        return True
    except Exception as e:
        logger.error(f"Failed to store JD embedding: {e}")
        return False


def find_similar_resumes(
    query_text: str,
    n_results: int = 5,
) -> List[Dict[str, Any]]:
    """Find resumes similar to the query text."""
    embeddings = generate_embeddings([query_text])
    if embeddings is None:
        return []
    try:
        collection = get_chroma_collection("resumes")
        results = collection.query(
            query_embeddings=embeddings,
            n_results=n_results,
        )
        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i] if results["documents"] else "",
                "distance": results["distances"][0][i] if results["distances"] else 0,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            })
        return output
    except Exception as e:
        logger.error(f"Similarity search error: {e}")
        return []


def match_resume_to_jd(
    resume_text: str,
    n_results: int = 5,
) -> List[Dict[str, Any]]:
    """Find job descriptions that best match a resume."""
    embeddings = generate_embeddings([resume_text])
    if embeddings is None:
        return []
    try:
        collection = get_chroma_collection("job_descriptions")
        results = collection.query(
            query_embeddings=embeddings,
            n_results=n_results,
        )
        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i] if results["documents"] else "",
                "distance": results["distances"][0][i] if results["distances"] else 0,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            })
        return output
    except Exception as e:
        logger.error(f"JD matching error: {e}")
        return []

"""
Database setup for SQLite (SQLAlchemy) and ChromaDB (vector store).
"""
import chromadb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings

# --- SQLite Setup ---
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency for FastAPI routes to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- ChromaDB Setup ---
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def get_chroma_collection(name: str = "resumes"):
    """Get or create a ChromaDB collection."""
    return chroma_client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def init_db():
    """Create all tables on startup."""
    from backend.models import user, resume, application, referral, template  # noqa
    Base.metadata.create_all(bind=engine)

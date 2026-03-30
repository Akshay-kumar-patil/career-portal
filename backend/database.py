"""
Database setup for SQLite (SQLAlchemy) and ChromaDB (vector store).
"""
import os
import chromadb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings

# FIX: echo=settings.DEBUG leaks all SQL to logs even in staging.
# Only enable when SQL_ECHO=true is explicitly set.
_echo_sql = settings.DEBUG and os.environ.get("SQL_ECHO", "false").lower() == "true"

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=_echo_sql,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def get_chroma_collection(name: str = "resumes"):
    return chroma_client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def init_db():
    from backend.models import user, resume, application, referral, template  # noqa
    Base.metadata.create_all(bind=engine)

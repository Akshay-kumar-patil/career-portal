"""
Career Automation & Job Intelligence Platform — FastAPI Backend
Main application entry point.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import init_db
from backend.ai.model_router import model_router

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered career automation platform with resume generation, job tracking, and AI insights.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root route
@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "auth": "/api/auth",
            "resume": "/api/resume",
            "analyzer": "/api/analyzer",
            "cover_letter": "/api/cover-letter",
            "applications": "/api/applications",
            "referrals": "/api/referrals",
            "interview": "/api/interview",
            "skills": "/api/skills",
            "analytics": "/api/analytics",
            "email": "/api/email",
            "github": "/api/github",
            "extract": "/api/extract",
            "ai_status": "/api/ai/status",
        }
    }


# Startup event
@app.on_event("startup")
def on_startup():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    logger.info("Database initialized")

    # Log AI status
    status = model_router.get_status()
    logger.info(f"AI Status: Internet={status['internet_available']}, Ollama={status['ollama_available']}, OpenAI Key={'✓' if status['openai_configured'] else '✗'}")


# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


# AI Status endpoint (no auth required for dashboard status)
@app.get("/api/ai/status")
def ai_status():
    return model_router.get_status()


# Register all routers
from backend.routers import auth, resume, analyzer, cover_letter, applications, referrals, interview, skills, analytics, email_gen, github_analyzer, extraction

app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(analyzer.router)
app.include_router(cover_letter.router)
app.include_router(applications.router)
app.include_router(referrals.router)
app.include_router(interview.router)
app.include_router(skills.router)
app.include_router(analytics.router)
app.include_router(email_gen.router)
app.include_router(github_analyzer.router)
app.include_router(extraction.router)

logger.info(f"Registered {len(app.routes)} routes")

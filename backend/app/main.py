"""
FastAPI application entrypoint for SentinelProctor AI.
Includes:
- Database initialization and staff provisioning on startup
- CORS configuration
- Authentication routes (Staff RBAC)
- Examination routes (Open student access + Protected teacher management)
- Proctoring & Multimodal inference routes
- Health & readiness endpoints
"""
import sys
from pathlib import Path

# Ensure project root and backend directory are on sys.path
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_BACKEND_DIR = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT_DIR), str(_BACKEND_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.api.routes import auth, exam, proctoring, results, session
from app.db.init_db import init_db

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Graceful startup and shutdown for database and inference workers."""
    logger.info("Initializing %s v%s (env=%s)...", settings.app_name, settings.app_version, settings.environment)
    init_db()
    logger.info("Database schemas and seed data ready.")
    yield
    logger.info("Gracefully shutting down %s...", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Scalable Multimodal AI Examination Proctoring Platform",
    lifespan=lifespan,
)

# Dynamic CORS configuration supporting Vercel and local origins
cors_origins = [
    settings.frontend_origin,
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
    "http://localhost:80",
    "http://localhost",
]
if settings.additional_origins:
    for orig in settings.additional_origins.split(","):
        clean_orig = orig.strip()
        if clean_orig and clean_orig not in cors_origins:
            cors_origins.append(clean_orig)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registration
app.include_router(auth.router)
app.include_router(exam.router)
app.include_router(proctoring.router)
app.include_router(results.router)
app.include_router(session.router)


@app.get("/health")
def health_check() -> dict:
    """Liveness probe: verifies API process is alive."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "heavy_ai_enabled": settings.enable_heavy_ai,
    }


@app.get("/health/ready")
def readiness_check() -> dict:
    """Readiness probe: verifies database connectivity and system readiness."""
    from app.db.session import SessionLocal
    from sqlalchemy import text
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ready" if db_status == "connected" else "degraded",
        "database": db_status,
        "service": settings.app_name,
        "version": settings.app_version,
        "heavy_ai_enabled": settings.enable_heavy_ai,
    }

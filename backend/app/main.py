"""
FastAPI application entrypoint.

Phase 0 scope: app wiring, CORS, and a real health-check endpoint.
No ML inference is imported or called here (RULE 3).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.api.routes import session, proctoring, results

setup_logging()
logger = get_logger(__name__)
settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router)
app.include_router(proctoring.router)
app.include_router(results.router)


@app.get("/health")
def health_check() -> dict:
    """Required by Phase 0 completion criteria: backend health endpoint must work."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.on_event("startup")
def on_startup() -> None:
    logger.info("%s v%s starting up (env=%s)", settings.app_name, settings.app_version, settings.environment)

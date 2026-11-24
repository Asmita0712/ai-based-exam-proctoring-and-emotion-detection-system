"""
Database session management with connection pooling.
Supports PostgreSQL for production and SQLite for local development/testing.
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()

db_url = settings.database_url
# Neon and Render PostgreSQL connection strings typically start with postgres://
# SQLAlchemy 1.4+ requires postgresql://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
engine_kwargs = {"pool_pre_ping": True}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # Optimized for Neon Serverless PostgreSQL & Free Tier:
    # Neon free tier terminates idle connections after ~5m and limits max connections.
    engine_kwargs.update(
        {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 300,  # Refresh connections before Neon compute sleeps
        }
    )
    # Ensure SSL is active for cloud PostgreSQL (Neon, Render, Supabase)
    if (
        "sslmode" not in db_url
        and "localhost" not in db_url
        and "127.0.0.1" not in db_url
    ):
        connect_args["sslmode"] = "require"

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """FastAPI dependency for scoped database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

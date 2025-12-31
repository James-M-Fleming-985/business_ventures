"""
Database configuration and session management for Feasibility Platform
Supports both SQLite (development) and PostgreSQL (production)
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - fallback to SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./feasibility_platform.db"
)

# Handle Railway/Heroku PostgreSQL URLs (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI routes to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from .models import User, Baseline, ExplorationHistory  # Import models
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager, asynccontextmanager
from typing import AsyncGenerator
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://p2p_user:p2p_pass@localhost:5432/p2p_automation")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def get_session():
    """Get database session (sync, for direct use)."""
    return SessionLocal()


@contextmanager
def get_db():
    """Get database session as context manager."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database."""
    from .models import Base
    Base.metadata.create_all(bind=engine)

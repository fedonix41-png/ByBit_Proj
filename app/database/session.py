"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from contextlib import contextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://p2p_user:p2p_pass@localhost:5432/p2p_automation")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def get_session() -> Session:
    """Get database session (sync, for direct use)."""
    return SessionLocal()


def get_db() -> Session:
    """FastAPI dependency for database session.
    
    Usage in endpoints:
        @router.get("/")
        async def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Get database session as context manager (for non-FastAPI code)."""
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

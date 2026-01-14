"""Database connection and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings
from src.db.models import Base

engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

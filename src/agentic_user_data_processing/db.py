"""
SQLAlchemy database utilities for the agent service.
"""
import os
from contextlib import contextmanager
from typing import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://finwhiz:finwhiz@localhost:5432/finwhiz")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

Base = declarative_base()


def init_db() -> None:
    """Create tables if they do not already exist."""
    from . import models  # noqa: F401  (ensure model metadata is registered)

    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope for raw scripts."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency providing a transactional session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

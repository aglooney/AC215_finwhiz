"""
SQLAlchemy database utilities for the FinWhiz agent service (Cloud-only version).
"""
import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# Expect the following environment variables to be set in Cloud Run:
#   DB_USER=postgres
#   DB_PASS=<YOUR_PASSWORD>
#   DB_NAME=finwhiz_db
#   DB_HOST=/cloudsql/YOUR_PROJECT:REGION:finwhiz-postgres

# If any of these are missing, fail fast to avoid accidental misconfiguration.
required_vars = ["DB_USER", "DB_PASS", "DB_NAME", "DB_HOST"]
missing = [v for v in required_vars if not os.getenv(v)]
if missing:
    raise RuntimeError(f"Missing required database env vars: {', '.join(missing)}")

DB_USER = os.environ["DB_USER"]
DB_NAME = os.environ["DB_NAME"]
DB_HOST = os.environ["DB_HOST"]

# Support both direct password or file-based secret
db_pass_value = os.environ["DB_PASS"]
# Check if DB_PASS is a file path or the actual password
if os.path.isfile(db_pass_value):
    with open(db_pass_value, "r") as f:
        DB_PASS = f.read().strip()
else:
    # Assume it's the password directly
    DB_PASS = db_pass_value

# Cloud SQL connection string via Unix socket path
DATABASE_URL =  f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# --- SQLAlchemy engine and session setup ---
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # auto-reconnects dropped connections
    pool_size=5,
    max_overflow=2,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


def init_db() -> None:
    """Create tables if they do not already exist."""
    from . import models  # noqa: F401 (ensures model metadata is loaded)
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope for scripts."""
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


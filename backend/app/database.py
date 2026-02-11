"""
Database setup module.

Provides a synchronous SQLAlchemy engine, a scoped session factory,
a declarative ``Base`` class for models, and a FastAPI dependency
(``get_db``) that yields one session per request.

TimescaleDB is wire-compatible with PostgreSQL so the standard
``postgresql://`` scheme works out of the box.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

# ── Naming convention for Alembic auto-generated constraints ────────────
convention: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)

# ── Engine ──────────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# ── Session factory ─────────────────────────────────────────────────────
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# ── Declarative base ───────────────────────────────────────────────────
Base: Any = declarative_base(metadata=metadata)


# ── FastAPI dependency ──────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and ensure it is closed after the request.

    Usage in a FastAPI route::

        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

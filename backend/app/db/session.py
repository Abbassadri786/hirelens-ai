from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _engine_options() -> dict[str, Any]:
    """Engine kwargs valid for the configured dialect.

    `pool_size` and `max_overflow` belong to `QueuePool` and raise a TypeError on
    dialects that use a different pool -- SQLite defaults to `SingletonThreadPool`,
    passing them unconditionally makes the engine constructible only against
    PostgreSQL, which breaks any non-Postgres URL at import time.
    """
    options: dict[str, Any] = {
        "pool_pre_ping": True,
        "future": True,
        # Never echo SQL in production: bound parameters include resume text.
        "echo": settings.DEBUG and not settings.is_production,
    }

    if settings.DATABASE_URL.startswith("sqlite"):
        return options

    options.update(
        {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            # Recycle below the typical managed-Postgres idle timeout so a
            # pooled connection is never handed out already dead.
            "pool_recycle": 1800,
        }
    )
    return options


engine = create_engine(settings.DATABASE_URL, **_engine_options())  # type: ignore[arg-type]

SessionFactory = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a session per request.

    Rolls back on an unhandled exception so a failed request cannot leak a
    partially applied transaction into the next user of the connection.
    """
    db = SessionFactory()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
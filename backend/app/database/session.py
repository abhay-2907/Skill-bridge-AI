"""
CareerPilot AI — Database Session
====================================
What is this?
  SQLAlchemy async session factory and FastAPI dependency for DB access.

Why async?
  FastAPI is built on async I/O (asyncio). Using sync SQLAlchemy would block
  the event loop, killing performance. asyncpg + SQLAlchemy async = non-blocking DB.

How it works:
  AsyncEngine → creates connections to PostgreSQL
  AsyncSessionLocal → factory that creates individual session objects
  get_db() → yields a session, commits on success, rolls back on error, always closes

Interview tip:
  Q: Why use a context manager for DB sessions?
  A: Guarantees the connection is always returned to the pool even if an error occurs.
     Without it, you'd leak connections and eventually exhaust the pool.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
# echo=True logs all SQL in development — set to False in production
# ── Engine ────────────────────────────────────────────────────────────────────
# For SQLite: use connect_args to allow multi-threaded access
# For PostgreSQL: use pool_size and max_overflow

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
    )

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit (safer for async)
    autocommit=False,
    autoflush=False,
)


# ── Base class for all ORM models ─────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """
    Dependency that provides a DB session per request.
    Automatically commits on success, rolls back on exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

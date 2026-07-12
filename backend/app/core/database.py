"""Async SQLAlchemy database engine and session factory with SQLite fallback."""
import socket
from urllib.parse import urlparse
import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

log = structlog.get_logger()


class Base(DeclarativeBase):
    pass


def is_postgres_reachable(db_url: str) -> bool:
    """Synchronously test if PostgreSQL port is reachable."""
    if "postgresql" not in db_url:
        return False
    try:
        parsed = urlparse(db_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except Exception:
        return False


# Determine database URL (use SQLite fallback if PG is down)
db_url = settings.DATABASE_URL
if "postgresql" in db_url and not is_postgres_reachable(db_url):
    log.warning(
        "PostgreSQL is unreachable (Docker might be stopped). Falling back to local SQLite.",
        url=db_url
    )
    db_url = "sqlite+aiosqlite:///./futurelens.db"
else:
    log.info("Connecting to PostgreSQL database", url=db_url)

engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    # pool_size/max_overflow are not supported by SQLite NullPool/StaticPool
    **({} if "sqlite" in db_url else {"pool_size": 10, "max_overflow": 20})
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


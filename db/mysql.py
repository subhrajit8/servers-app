from collections.abc import AsyncGenerator

import os

from dotenv import load_dotenv
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    create_async_engine,
)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

database_url = make_url(DATABASE_URL).set(drivername="mysql+asyncmy")

engine: AsyncEngine = create_async_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=7,
    max_overflow=10,
    pool_timeout=50,
    pool_recycle=3000,
)


async def check_connection(db_engine: AsyncEngine) -> None:
    """Verify DB is reachable; raise so the app does not start."""
    try:
        async with db_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(f"Database connection failed: {e}") from e


async def get_db() -> AsyncGenerator[AsyncConnection, None]:
    """Check out a pooled connection for one request, then return it to the pool."""
    async with engine.connect() as conn:
        yield conn

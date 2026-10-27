from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine: Engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size= 7,
    max_overflow= 10,
    pool_timeout= 50,
    pool_recycle= 3000,
)

def check_connection(db_engine: Engine) -> None:
    """Verify DB is reachable; raise so the app does not start."""
    try:
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(f"Database connection failed: {e}") from e


def get_db() -> Generator[Connection, None, None]:
    """Check out a pooled connection for one request, then return it to the pool."""
    with engine.connect() as conn:
        yield conn

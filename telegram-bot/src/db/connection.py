import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

_engine: AsyncEngine | None = None


def get_database_url() -> str:
    db_path = os.getenv("SQLITE_PATH", "./data/telegram-bot.sqlite3")
    resolved = Path(db_path).expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{resolved}"


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_database_url())
    return _engine

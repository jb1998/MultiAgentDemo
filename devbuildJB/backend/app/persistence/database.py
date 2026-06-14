from collections.abc import AsyncGenerator

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings
from app.models.task import Base

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Lightweight SQLite migrations for columns added after initial schema
_SQLITE_COLUMN_MIGRATIONS: list[tuple[str, str, str]] = [
    ("tasks", "trace_id", "VARCHAR(32)"),
]


def _apply_sqlite_migrations(connection) -> None:
    inspector = inspect(connection)
    for table, column, col_type in _SQLITE_COLUMN_MIGRATIONS:
        if table not in inspector.get_table_names():
            continue
        existing = {c["name"] for c in inspector.get_columns(table)}
        if column not in existing:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_apply_sqlite_migrations)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

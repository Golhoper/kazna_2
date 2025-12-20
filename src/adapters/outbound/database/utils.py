from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from adapters.config.settings import settings


def create_engine_and_session_factory() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Создает engine и session_factory."""
    engine = create_async_engine(
        settings.db.url,
        pool_size=20,
        pool_pre_ping=True,
        pool_use_lifo=True,
        echo=settings.db.echo,
    )
    async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
    return engine, async_session_factory

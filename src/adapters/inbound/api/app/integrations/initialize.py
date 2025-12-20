from fastapi import FastAPI
from loguru import logger
from starlette.requests import Request

from adapters.outbound.database.utils import create_engine_and_session_factory
from adapters.outbound.redis.client import AsyncRedisClient
from core.shared_kernel.units_of_work.postgres import UnitOfWork


def setup_postgres(app: FastAPI) -> None:
    """Создает подключение к базе данных PostgreSQL.

    Эта функция создает экземпляр SQLAlchemy engine,
    фабрику сессий (session_factory) для создания сессий,
    и сохраняет их в свойстве state приложения FastAPI.
    """
    engine, session_factory = create_engine_and_session_factory()
    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    logger.info("SQLAlchemy Engine и Session Factory созданы и сохранены в app.state")


def setup_uow(app: FastAPI) -> None:
    """Записывает `UnitOfWork` в `app.state`."""
    app.state.uow_class = UnitOfWork


def setup_redis(app: FastAPI) -> None:
    """Создает подключение к Redis."""
    app.state.redis_client = AsyncRedisClient()


async def initialize_integrations(app: FastAPI) -> None:
    """Инициализирует интеграции приложения."""
    setup_postgres(app)
    setup_uow(app)
    setup_redis(app)
    logger.info("Все интеграции успешно инициализированы")


def get_uow_from_request(request: Request) -> UnitOfWork:
    """Возвращает uow из запроса."""
    return request.app.state.uow_class(request.app.state.db_session_factory)


def get_redis_client(request: Request) -> AsyncRedisClient:
    """Возвращает клиент Redis."""
    return request.app.state.redis_client

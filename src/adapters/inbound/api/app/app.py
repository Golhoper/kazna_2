from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from loguru import logger

from __version__ import __version__
from adapters.inbound.api.app.exception_handlers import register_common_exception_handlers
from adapters.inbound.api.app.integrations.initialize import initialize_integrations
from adapters.inbound.api.app.integrations.teardown import teardown_integrations
from adapters.inbound.api.app.middlewares.setup import setup_middlewares
from adapters.inbound.api.app.router import api_router


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Контекстный менеджер Lifespan для управления запуском и остановкой приложения."""
    await initialize_integrations(app)
    logger.info("Приложение настроено")
    yield  # Приложение работает здесь
    await teardown_integrations(app)
    logger.info("Приложение остановлено")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Казна 2.0",
        version=__version__,
        lifespan=_lifespan,
        swagger_ui_parameters={
            "defaultModelsExpandDepth": 0,  # Скрыть модели по умолчанию
            "showExtensions": True,  # Показать расширения
            "filter": True,  # Включить фильтр по тегам
            "displayRequestDuration": True,  # Показать длительность запроса
        },
        default_response_class=ORJSONResponse,
    )
    setup_middlewares(app)
    app.include_router(api_router)
    register_common_exception_handlers(app)
    return app

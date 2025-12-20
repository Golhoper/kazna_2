from fastapi import FastAPI
from loguru import logger


async def stop_postgres(app: FastAPI) -> None:
    """Корректно закрывает пул соединений SQLAlchemy engine.

    Вызывается при остановке приложения FastAPI для освобождения ресурсов базы данных.
    """
    if hasattr(app.state, "db_engine") and app.state.db_engine:
        logger.info("Закрытие пула соединений PostgreSQL")
        await app.state.db_engine.dispose()
        logger.info("Пул соединений PostgreSQL успешно закрыт")
    else:
        logger.warning("Экземпляр SQLAlchemy engine не найден в app.state.db_engine при остановке")


async def stop_redis(app: FastAPI) -> None:
    await app.state.redis_client.close()


async def teardown_integrations(app: FastAPI) -> None:
    """Останавливает интеграции приложения."""
    await stop_postgres(app)
    await stop_redis(app)
    logger.info("Все интеграции остановлены")

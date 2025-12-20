"""Модуль для настройки и добавления Middleware к приложению FastAPI."""

from fastapi import FastAPI
from loguru import logger

from adapters.inbound.api.app.middlewares.cors import setup_cors


def setup_middlewares(app: FastAPI) -> None:
    """Агрегирующая функция для добавления всех необходимых Middleware."""
    setup_cors(app)
    logger.info("CORS Middleware успешно добавлена")

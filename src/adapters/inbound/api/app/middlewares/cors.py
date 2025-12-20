from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    """Настраивает и добавляет CORSMiddleware к приложению FastAPI.

    Разрешает запросы со всех источников, методов и заголовков.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Разрешенные источники (домены). "*" разрешает все
        allow_methods=["*"],  # Разрешенные HTTP методы (GET, POST, etc). "*" разрешает все
        allow_credentials=True,  # Разрешает передачу cookie в кросс-доменных запросах
        allow_headers=["*"],  # Разрешенные HTTP заголовки. "*" разрешает все
    )
    logger.info("CORS Middleware успешно добавлена")

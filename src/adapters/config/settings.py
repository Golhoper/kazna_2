import pathlib
from typing import Annotated
from urllib.parse import quote_plus

from dotenv import load_dotenv
from loguru import logger
from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class DatabaseSettings(BaseSettings):
    """Настройки подключения к базе данных."""

    model_config = SettingsConfigDict(env_prefix="database_")
    name: Annotated[str, Field(default="dev", description="Имя базы данных")]
    username: Annotated[str, Field(default="dev", description="Имя пользователя для подключения к БД")]
    password: Annotated[str, Field(default="dev", description="Пароль для подключения к БД")]
    host: Annotated[str, Field(default="localhost", description="Хост базы данных")]
    port: Annotated[int, Field(default=5432, description="Порт базы данных")]
    echo: Annotated[bool, Field(default=False, description="Флаг для включения/выключения логирования SQL запросов SQLAlchemy")]

    @property
    def url(self) -> str:
        """Генерирует URL для подключения к базе данных PostgreSQL с использованием asyncpg."""
        db_url = URL.create(
            drivername="postgresql+asyncpg",
            database=self.name,
            username=self.username,
            password=quote_plus(self.password),  # Экранирование пароля для URL
            host=self.host,
            port=self.port,
        ).render_as_string(hide_password=False)
        url: str = db_url
        return url


class RedisSettings(BaseSettings):
    """Настройки подключения к Redis."""

    model_config = SettingsConfigDict(env_prefix="redis_")
    url: RedisDsn = Field(description="URL для подключения к Redis")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", str_strip_whitespace=True)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings, description="Настройки базы данных")
    # redis: RedisSettings = Field(default_factory=RedisSettings, description="Настройки Redis")


# # Вычисляет путь к .env файлу из родительской директории
# settings_dir = pathlib.Path(__file__).parent
# env_path = settings_dir.parent.parent.parent / ".env"

# # Явно загрузить переменные из .env файла
# if env_path.exists():
#     load_dotenv(dotenv_path=env_path)
#     logger.info("Переменные окружения загружены из .env файла")
# else:
#     logger.info("Не найден .env файл. Используются только переменные окружения")

# Экземпляр настроек, загружаемых из переменных окружения и .env файла, если он есть.
settings = Settings()

from typing import Any

from redis.asyncio import Redis

from adapters.config.settings import settings


class AsyncRedisClient:
    """Асинхронный клиент-обертка для взаимодействия с Redis.

    Предоставляет упрощенный интерфейс для основных операций Redis.
    """

    def __init__(self) -> None:
        """Инициализирует асинхронный клиент Redis на основе URL из настроек."""
        self.client = Redis.from_url(url=settings.redis.url.encoded_string())

    async def set(
        self,
        key: str,
        value: Any,
        expires: int | None = None,
        nx: bool = False,
    ) -> Any:
        """Устанавливает значение ключа в Redis с опциональным временем жизни.

        Если expires < 1, время жизни не устанавливается.
        Параметр nx=True устанавливает значение только если ключ не существует.
        """
        expires = None if expires is not None and expires < 1 else expires
        return await self.client.set(key, value, ex=expires, nx=nx)

    async def get(self, key: str) -> Any:
        """Получает значение ключа из Redis."""
        return await self.client.get(key)

    async def delete(self, key: str) -> Any:
        """Удаляет ключ из Redis."""
        return await self.client.delete(key)

    async def close(self) -> None:
        """Закрывает соединение с Redis."""
        await self.client.aclose()  # type: ignore[attr-defined]

    async def ttl(self, key: str) -> int | Any:
        """Возвращает оставшееся время жизни ключа в секундах.

        Возвращает -1, если у ключа нет времени жизни.
        Возвращает -2, если ключ не существует.
        """
        return await self.client.ttl(key)

from starlette.requests import Request

from adapters.outbound.redis.client import AsyncRedisClient
from core.shared_kernel.units_of_work.postgres import UnitOfWork


def get_uow_from_request(request: Request) -> UnitOfWork:
    """Возвращает uow из запроса."""
    return request.app.state.uow_class(request.app.state.db_session_factory)


def get_redis_client(request: Request) -> AsyncRedisClient:
    """Возвращает клиент Redis."""
    return request.app.state.redis_client

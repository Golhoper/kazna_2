from typing import TypeVar

from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from generic.database.repositories.sa_repositories.base_criteria import (
    BaseCriteria,
    TEntityId,
)

TSaModel = TypeVar("TSaModel", bound=DeclarativeBase)


async def get_all_from_db(session: AsyncSession, sa_model: type[TSaModel]) -> list[TSaModel]:
    """Возвращает все записи из БД."""
    statement = select(sa_model)
    result = await session.scalars(statement)
    return list(result.all())


async def exists_by_criteria(session: AsyncSession, sa_model: type[TSaModel], criteria: BaseCriteria | None) -> bool:
    """Проверяет наличие записей в БД по критериям."""
    result = await _get_by_criteria(session, sa_model, criteria, field="id")
    return bool(result.scalar())


async def get_by_criteria(
    session: AsyncSession, sa_model: type[TSaModel], criteria: BaseCriteria | None
) -> list[TSaModel]:
    """Возвращает список записей в БД по критериям."""
    result = await _get_by_criteria(session, sa_model, criteria)
    return list(result.unique().scalars().all())


async def get_ids_by_criteria(
    session: AsyncSession, sa_model: type[TSaModel], criteria: BaseCriteria | None
) -> set[TEntityId]:
    """Возвращает set id записей в БД по критериям."""
    result = await _get_by_criteria(session, sa_model, criteria, field="id")
    return set(result.unique().scalars().all())


async def get_names_by_criteria(
    session: AsyncSession, sa_model: type[TSaModel], criteria: BaseCriteria | None
) -> set[str]:
    """Возвращает set названий записей в БД по критериям."""
    result = await _get_by_criteria(session, sa_model, criteria, field="name")
    return set(result.unique().scalars().all())


async def _get_by_criteria(
    session: AsyncSession,
    sa_model: type[TSaModel],
    criteria: BaseCriteria | None,
    field: str | None = None,
) -> Result:
    query = select(getattr(sa_model, field)) if field else select(sa_model)
    if criteria:
        query = criteria.filter(query)
    return await session.execute(query)

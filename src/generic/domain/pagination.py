import math
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from generic.api.pydantic_models import CamelCasedAliasesModel

T = TypeVar("T")


class PageSizeIn(BaseModel):
    """Входные данные пагинации."""

    page: int = Field(default=1, ge=0, title="Номер страницы, >=1")
    size: int = Field(default=100)


class PageSizeOut(CamelCasedAliasesModel, BaseModel, Generic[T]):
    """Выходные данные пагинации."""

    items: Sequence[T]
    next_page: int | None = None
    previous_page: int | None = None
    count: int
    pages: int

    model_config = ConfigDict(ser_json_timedelta="iso8601")


def make_page_size_out(items: Sequence[Any], count: int, page_in: PageSizeIn) -> PageSizeOut:  # type:ignore[type-arg]
    """Возвращает модель с данными пагинации."""
    page = page_in.page if page_in else 1
    previous_page = page - 1 if page > 1 else None
    pages = math.ceil(count / float(page_in.size))
    next_page = page + 1 if page < pages else None

    return PageSizeOut(
        items=items,
        next_page=next_page,
        previous_page=previous_page,
        count=count,
        pages=pages,
    )

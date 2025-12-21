import enum
from typing import Annotated, cast

from pydantic import BaseModel, Field

from generic.api.pydantic_models import CamelCasedAliasesModel

ConIntPage = Annotated[int, Field(gt=0)]
ConIntSize = Annotated[int, Field(gt=9, lt=1000)]


class OrderingDirectionEnum(enum.Enum):
    """Направление сортировки SQL запроса."""

    asc = "asc"
    desc = "desc"


class OrderBySchema(CamelCasedAliasesModel):
    """Контракт сортировки запроса."""

    field_name: str
    direction: OrderingDirectionEnum


class PaginatePageParams(CamelCasedAliasesModel):
    page: ConIntPage = cast("ConIntPage", 1)
    size: ConIntSize = cast("ConIntSize", 20)
    order_by: OrderBySchema | None = None
    filters: type[BaseModel]

import datetime as dt
import uuid
from typing import Annotated, Any

import pydantic
from pydantic import ConfigDict, Field


class Event(pydantic.BaseModel):
    """Базовый класс для событий.

    - Запрещает объекту добавлять атрибуты, неописанные в классе.
    - Запрещает изменять значения атрибутов после инициализации объекта.
    """

    happened_on: dt.datetime = pydantic.Field(default_factory=dt.datetime.now)
    model_config = ConfigDict(frozen=True, extra="forbid")


class EntityChangedDataEvent(Event):
    entity_id: Annotated[uuid.UUID, Field(description="id сущности")]
    entity_type: Annotated[str, Field(description="Тип сущности (наименование таблицы в бд)")]
    changes: Annotated[dict[str, Any], Field(description="Какие изменения произошли")]

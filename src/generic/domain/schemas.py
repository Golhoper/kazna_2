from datetime import timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IdNameSchema(BaseModel):
    """Схема для возвращения id и name."""

    id: UUID | str | int
    name: str
    model_config = ConfigDict(from_attributes=True)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, IdNameSchema) and self.id == other.id


class UuidNameSchema(IdNameSchema):
    """Схема возвращения данных id (строго UUID) и name."""

    id: UUID


def timedelta_isoformat(td: timedelta) -> str:
    """Форматирует timedelta в isoformat, но без микросекунд."""
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{'-' if td.days < 0 else ''}P{abs(td.days)}DT{hours:d}H{minutes:d}M{seconds:d}"

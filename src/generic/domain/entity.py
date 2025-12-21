from typing import TypeVar
from uuid import UUID, uuid4

from generic.domain.mixins.log_changed_attrs import LogChangedAttrsMixin

TEntity = TypeVar("TEntity", bound="BaseEntity")


class BaseEntity(LogChangedAttrsMixin):
    """Базовый класс для сущности."""

    entity_type: str = NotImplemented  # Латиницей, в нижнем регистре, в единственном числе

    @property
    def id(self) -> UUID:
        """Id."""
        return self._id

    @id.setter
    def id(self, value: UUID) -> None:
        """Id (setter)."""
        self._id = value or uuid4()

    def validate(self) -> None:
        """Валидация сущности."""

    def __repr__(self) -> str:
        if hasattr(self, "name"):
            return f'{self.__class__.__name__}(id="{self.id}", name="{self.name}")'
        return f'{self.__class__.__name__}(id="{self.id}")'

    def __str__(self) -> str:
        return self.__repr__()

    def __hash__(self) -> int:
        return hash(f"{self.__class__.__name__}{self.id}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

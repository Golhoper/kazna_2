import datetime as dt
from typing import Any

from generic.utils.time_utils import now


class SoftDeleteMixin:
    """Миксин для сущностей с полями для пометки на удаление."""

    def __init__(
        self,
        *args: Any,
        is_deleted: bool,
        deleted_at: dt.datetime | None,
        **kwargs: Any,
    ) -> None:
        """Инициализация."""
        if is_deleted and not deleted_at:
            deleted_at = now()
        elif not is_deleted and deleted_at:
            is_deleted = True

        self._is_deleted = is_deleted
        self._deleted_at = deleted_at
        super().__init__(*args, **kwargs)

    @property
    def is_deleted(self) -> bool:
        """Признак удаления."""
        return self._is_deleted

    @is_deleted.setter
    def is_deleted(self, value: bool) -> None:
        """is_deleted (setter)."""
        self._is_deleted = value

        if value and not self.deleted_at:
            self.deleted_at = now()
        elif not value and self.deleted_at:
            self.deleted_at = None

    @property
    def deleted_at(self) -> dt.datetime | None:
        """Время Удаления."""
        return self._deleted_at

    @deleted_at.setter
    def deleted_at(self, value: dt.datetime | None) -> None:
        """deleted_at (setter)."""
        self._deleted_at = value

        if value and not self.is_deleted:
            self.is_deleted = True
        elif not value and self.is_deleted:
            self.is_deleted = False

import datetime as dt
from typing import Any

from generic.utils.time_utils import now


class ArchivedMixin:
    """Миксин для сущностей с полями для пометки архивности."""

    def __init__(
        self,
        *args: Any,
        is_archived: bool,
        archived_at: dt.datetime | None,
        **kwargs: Any,
    ) -> None:
        """Инициализация."""
        if is_archived and not archived_at:
            archived_at = now()
        elif not is_archived and archived_at:
            is_archived = True

        self._is_archived = is_archived
        self._archived_at = archived_at
        super().__init__(*args, **kwargs)

    @property
    def is_archived(self) -> bool:
        """Признак архивности."""
        return self._is_archived

    @is_archived.setter
    def is_archived(self, value: bool) -> None:
        """Признак архивности (setter)."""
        self._is_archived = value

        if value and not self.archived_at:
            self.archived_at = now()
        elif not value and self.archived_at:
            self.archived_at = None

    @property
    def archived_at(self) -> dt.datetime | None:
        """Время архивности."""
        return self._archived_at

    @archived_at.setter
    def archived_at(self, value: dt.datetime | None) -> None:
        """archived_at (setter)."""
        self._archived_at = value

        if value and not self.is_archived:
            self.is_archived = True
        elif not value and self.is_archived:
            self.is_archived = False

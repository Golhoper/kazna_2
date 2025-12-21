import datetime as dt
from typing import Any

from generic.utils.time_utils import now


class CreatedUpdatedMixin:
    """Миксин для сущностей с полями created_at и updated_at."""

    def __init__(
        self,
        *args: Any,
        created_at: dt.datetime | None,
        updated_at: dt.datetime | None,
        **kwargs: Any,
    ) -> None:
        """Инициализация."""
        self.created_at = created_at or now()
        self.updated_at = updated_at or now()
        super().__init__(*args, **kwargs)

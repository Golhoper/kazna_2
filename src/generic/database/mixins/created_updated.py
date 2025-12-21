from collections.abc import Callable
from datetime import UTC, datetime
from functools import partial

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

_now: Callable = partial(datetime.now, UTC)  # type:ignore[type-arg]


class SaCreatedUpdatedMixin:
    """Миксин с датами создания и обновления."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        default=_now,
        comment="Дата создания",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now,
        onupdate=_now,
        comment="Дата обновления",
    )

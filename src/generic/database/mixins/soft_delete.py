from datetime import datetime

from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression


class SaSoftDeleteMixin:
    """Миксин с полями для пометки на удаление."""

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        server_default=expression.false(),
        comment="Признак удаления",
    )
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
        comment="Дата удаления",
    )

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression


class SaArchivedMixin:
    """Миксин с полями для пометки архивности."""

    is_archived: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
        server_default=expression.false(),
        comment="Признак архивности",
    )
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
        comment="Дата архивирования",
    )

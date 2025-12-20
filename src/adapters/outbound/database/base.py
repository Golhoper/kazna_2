from datetime import datetime
from typing import TypeVar

from sqlalchemy import DECIMAL, DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase, registry

sa_meta = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    },
)


class SaBase(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""

    metadata = sa_meta
    registry = registry(type_annotation_map={datetime: DateTime(timezone=True)})


TSaModel = TypeVar("TSaModel", bound=DeclarativeBase)
SaDecimal_18_2 = DECIMAL(18, 2)

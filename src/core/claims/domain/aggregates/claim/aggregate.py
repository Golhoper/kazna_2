import datetime as dt

from typing import Self

from core.claims.domain.aggregates.claim.entities.payment_item.entity import PaymentItem
from core.claims.domain.aggregates.claim.types import ClaimId

from generic.domain.entity import BaseEntity
from generic.domain.mixins.created_updated import CreatedUpdatedMixin
from generic.domain.mixins.soft_delete import SoftDeleteMixin


class Claim(SoftDeleteMixin, CreatedUpdatedMixin, BaseEntity):
    """Корень агрегата `Заявка`."""

    def __init__(
        self: Self,
        id: ClaimId,
        system_number: str,
        payment_items: list[PaymentItem] | None = None,
        created_at: dt.datetime | None = None,
        updated_at: dt.datetime | None = None,
        is_deleted: bool = False,
        deleted_at: dt.datetime | None = None,
    )-> None:
        self.id = id 
        self.system_number = system_number
        self.payment_items = payment_items or []
        super().__init__(
            created_at=created_at,
            updated_at=updated_at,
            is_deleted=is_deleted,
            deleted_at=deleted_at,
        )

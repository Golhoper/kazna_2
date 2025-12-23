import datetime as dt
from typing import Self
from core.claims.domain.aggregates.claim.entities.payment_item.types import PaymentItemId
from generic.domain.entity import BaseEntity
from generic.domain.mixins.created_updated import CreatedUpdatedMixin


class PaymentItem(CreatedUpdatedMixin, BaseEntity):
    """Сущность `Предмет оплаты `."""

    def __init__(
        self: Self, 
        id: PaymentItemId,
        created_at: dt.datetime | None = None,
        updated_at: dt.datetime | None = None,
    ) -> None:
        self.id = id
        super().__init__(created_at=created_at, updated_at=updated_at)

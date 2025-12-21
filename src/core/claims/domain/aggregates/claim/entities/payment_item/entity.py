from typing import Self
from core.claims.domain.aggregates.claim.entities.payment_item.types import PaymentItemId
from generic.domain.entity import BaseEntity


class PaymentItem(BaseEntity):
    """Сущность `Предмет оплаты `."""

    def __init__(
        self: Self, 
        id: PaymentItemId,
        crea
    )
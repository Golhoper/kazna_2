from uuid import UUID
from enum import Enum

class ClaimStatusEnum(Enum):
    draft = "draft"
    on_approval = "on_approval"
    approved = "approved"
    on_payment = "on_payment"
    payed = "payed"
    rejected = "rejected"
    partialy_paid = "partialy_paid"


class Claim:
     def __init__(
        self, id: UUID, number: int, payment_items: list, total_sum: int, status: ClaimStatusEnum
    ) -> None:
        self.id = id
        self.number = number
        self.payment_items = payment_items
        self.status = status
        self.total_sum = total_sum
        
    
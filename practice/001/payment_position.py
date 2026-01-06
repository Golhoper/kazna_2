from uuid import UUID
from enum import Enum

class PaymentPositionStatusEnum(Enum):
    draft = "draft"
    in_registry = "in_registry"
    on_payment = "on_payment"
    payed = "payed"
    rejected = "rejected"

class PaymentPosition:
     def __init__(
        self, id: UUID, number: int, total_sum: int, status: PaymentPositionStatusEnum
    ) -> None:
        self.id = id
        self.number = number
        self.status = status
        self.total_sum = total_sum
        
    
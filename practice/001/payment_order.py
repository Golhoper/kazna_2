from uuid import UUID
from enum import Enum

class PaymentOrderStatusEnum(Enum):
    create = "create"
    pending = "pending"
    payed = "payed"    


class PaymentOrder:
     def __init__(
        self, id: UUID, payment_registry:list,  status: PaymentOrderStatusEnum, total_sum: int
    ) -> None:
        self.id = id
        self.payment_registry = payment_registry
        self.status = status
        self.total_sum = total_sum 
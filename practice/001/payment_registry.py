from uuid import UUID
from enum import Enum

class PaymentRegistryStatusEnum(Enum):
    draft = "draft"
    on_approval = "on_approval"
    approved = "approved"
    on_payment = "on_payment"
    payed = "payed"
    


class PaymentRegistry:
     def __init__(
        self, id: UUID, payment_positions:list,  status: PaymentRegistryStatusEnum
    ) -> None:
        self.id = id
        self.payment_positions = payment_positions
        self.status = status
        

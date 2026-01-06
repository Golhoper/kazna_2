from uuid import UUID


class PaymentItem:
     def __init__(
        self, id: UUID, payment_positions: list, total_sum: int
    ) -> None:
        self.id = id
        self.payment_positions = payment_positions
        self.total_sum = total_sum
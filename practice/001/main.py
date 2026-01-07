from claim import Claim
import uuid 
from claim import ClaimStatusEnum
from payment_item import PaymentItem
from payment_position import PaymentPosition, PaymentPositionStatusEnum
from payment_registry import PaymentRegistry, PaymentRegistryStatusEnum
from payment_order import PaymentOrder, PaymentOrderStatusEnum

#тут надо писать какую-то логику (например создание заявки с его атрибутивным составом)
def main() -> None:
    claim1 = Claim(
        id=uuid.uuid4(), number=1, payment_items=[], total_sum=0, status=ClaimStatusEnum.draft
    )
    claim1.total_sum = 10
    
    payment_item1 = PaymentItem(
        id=uuid.uuid4(), payment_positions=[], total_sum=0
    )
    payment_item1.total_sum = 10
    payment_item2 = PaymentItem(
        id=uuid.uuid4(), payment_positions=[], total_sum=0
    )
    payment_item2.total_sum = 20

    claim1.payment_items = [payment_item1, payment_item2]

    claim1.status = ClaimStatusEnum.on_approval

    payment_position1 = PaymentPosition(
        id=uuid.uuid4(), number=1, total_sum=10, status=PaymentPositionStatusEnum.draft
    )

    payment_item1.payment_positions = [payment_position1]

    payment_position1 = PaymentPosition(
        id=uuid.uuid4(), number=2, total_sum=20, status=PaymentPositionStatusEnum.draft
    )

    payment_item2.payment_positions = [payment_position1]

    claim1.status = ClaimStatusEnum.approved
    payment_position1.status = PaymentPositionStatusEnum.in_registry

    payment_registry1 = PaymentRegistry(
        id=uuid.uuid4(), payment_positions=[payment_position1], status=PaymentRegistryStatusEnum.on_approval
    )
    payment_registry1.status = PaymentRegistryStatusEnum.approved

    payment_order1 = PaymentOrder(
        id=uuid.uuid4(), payment_registry=[payment_registry1], status=PaymentOrderStatusEnum.create, total_sum=20
    )
    payment_order1.status = PaymentOrderStatusEnum.pending

    payment_order1.status = PaymentOrderStatusEnum.payed
    payment_registry1.status = PaymentRegistryStatusEnum.payed
    payment_position1.status = PaymentPositionStatusEnum.payed
    claim1.status = ClaimStatusEnum.partialy_paid

    claim2 = Claim(
        id=uuid.uuid4(), number=2, payment_items=[], total_sum=0, status=ClaimStatusEnum.draft
    )
    payment_item3 = PaymentItem(
         id=uuid.uuid4(), payment_positions=[], total_sum=3
    )
    claim2.total_sum = 3
    claim2.status = ClaimStatusEnum.on_approval
    payment_position2 = PaymentPosition(
         id=uuid.uuid4(), number=3, total_sum=3, status=PaymentPositionStatusEnum.draft
    )
    claim2.status = ClaimStatusEnum.rejected
    payment_position2.status = PaymentPositionStatusEnum.rejected
    print("done")

    
main()
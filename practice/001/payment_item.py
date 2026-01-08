import uuid
from enum import Enum

class PaymentItemVat(Enum):
    five = 5
    ten = 10
    twenty = 20

class PaymentItem:
    def __init__(
        self, id: uuid.UUID, payment_positions: list, price: int, quantity: int, vat: PaymentItemVat
    ) -> None:
        self.id = id
        self.payment_positions = payment_positions
        self.price = price
        self.quantity = quantity
        self.vat = vat 

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if value < 0:
            raise ValueError("Цена не может быть отрицательной")
        self._price = value

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        if value < 0:
            raise ValueError("Кол-во не может быть отрицательным")
        self._quantity = value
    
    @property
    def total_sum(self):
        total_sum = self.price * self.quantity
        return total_sum

    @property
    def sum_vat(self):
        sum_vat = (self.total_sum * self.vat.value) / (100 + self.vat.value)
        return sum_vat

    @property
    def sum_without_vat(self):
        sum_without_vat = self.total_sum - self.sum_vat
        return sum_without_vat  

def main():
    payment_item1 = PaymentItem(
        id=uuid.uuid4(), payment_positions=[], price=0, quantity=0, vat=PaymentItemVat.ten
    )
    a = 1
    assert payment_item1.sum_vat == 0     
    assert payment_item1.total_sum == 0 
    assert payment_item1.sum_without_vat == 0 
    
    payment_item1.price = 1
    payment_item1.quantity = 88


    assert payment_item1.sum_vat == 8
    assert payment_item1.total_sum == 88
    assert payment_item1.sum_without_vat == 80

main()
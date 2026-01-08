class BankAccount:
    def __init__(self, balance):
        self._balance = balance 
    
    @property
    def balance(self):
        return self._balance*5

    @balance.setter
    def balance(self, value):
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = value

bc = BankAccount(1)
bc.balance=2
print(bc.balance)

# геттеры и сеттеры нужны чтобы контролировать доступ к атрибутам и валидировать данные.
#Идея геттеров и сеттеров (очень простыми словами)

# Если нужно
#	•	читать значение → разрешать
#	•	менять значение → проверять
#
# Для этого и нужны:
#	•	геттер — получить значение
#	•	сеттер — установить значение
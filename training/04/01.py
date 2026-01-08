# 1) Что такое __new__ (new вряд ли встретишь, просто на собезах спрашивают) и __init__
#__new__ создаёт объект,
#__init__ инициализирует его.

class MyClass:
    def __new__(cls):
        print("Шаг 1: __new__")
        return super().__new__(cls)
MyClass()
#📌 cls — это сам класс, не объект

class MyClass1:
    def __init__(self):
        print("Шаг 2: __init__")
MyClass1()
#📌 self — это уже созданный объект



class Example:
    def __new__(cls):
        print("1. __new__ — создаём объект")
        return super().__new__(cls)

    def __init__(self):
        print("2. __init__ — настраиваем объект")
obj = Example()

class User:
    def __new__(cls, name):
        print("Создание объекта")
        return super().__new__(cls)
        
    def __init__(self, name):
        print(f"Инициализация пользователя: {name}")
        self.name = name

user = User("Alex")
print(f"Имя пользователя: {user.name}")


def my_decorator(func):
    def wrapper():
        print("Функция началась")
        func()
        print("Функция закончилась")
    return wrapper

@my_decorator
def say_hello():
    print("Привет!")

say_hello()
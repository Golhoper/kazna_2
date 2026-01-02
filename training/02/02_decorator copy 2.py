def my_decorator(func):
    counter=1
    def wrapper():
        nonlocal counter  # Указываем, что хотим изменять переменную из внешней области видимости
        print("Функция вызывалась", counter, "раз")
        func()
        counter+=1
    return wrapper

@my_decorator
def say_hi():
    print("Zdarova")
say_hi()
say_hi()
say_hi()
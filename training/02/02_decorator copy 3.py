def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Function start")
        func(*args, **kwargs)
        print("Function end")
        pass
    return wrapper


@my_decorator
def greet(name, age):
    print(f"Привет, {name}. Тебе {age} лет.")


greet("Аня", 10)


#Кортеж - по сути тот же самый список, но его нельзя менять или добавлять в него что-то!
#*args — всё по порядку
#**kwargs — всё по именам

my_tuple = ("Lexa", 25, "QA")
print(my_tuple[0])
print(my_tuple[1])
print(my_tuple[2])
def my_decorator(func):
    def wrapper():
        print("Nachalo")
        func()
        print("Konec")
    return wrapper

@my_decorator
def say_hi():
    print("hi")

say_hi()
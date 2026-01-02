class Cat:
    total_cats = 0

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
        self.is_hungry = True
        Cat.total_cats += 1

    def meow(self):
        print(f"{self.name} говорит: Мяу!")

    def eat(self, food):
        if self.is_hungry:
            print(f"{self.name} хавает {food}")
            self.is_hungry = False
        else:
            print(f"{self.name} нажрался как свинота")

    def get_info(self):
        return f"Имя: {self.name} Возвраст: {self.age} Голоден: {self.is_hungry}"

    def set_age(self, new_age: int):
        if new_age > 0:
            self.age = new_age
        else:
            print("Возвраст должен быть больше 0")

    def get_age(self):
        return f"У {self.name}а новый вовзраст={self.age}"
    @classmethod
    def create_kitten(cls, name: str, age: int):
      return cls(name, age)


cat1 = Cat("Jeka", 35)
cat2 = Cat("Lexa", 25)
cat1.name = "Jekichan"
cat3 = Cat.create_kitten("Lena", 1)

print(cat1.name, cat1.age)
print(cat2.name, cat2.age)
cat1.meow()
cat2.meow()
cat1.eat("рыбу")
cat2.eat("котлету")
cat1.eat("творог")
print(Cat.total_cats)
print(cat1.get_info())
print(cat2.get_info())
cat1.set_age(40)
print(cat1.get_age())
print(cat3.name, cat3.age)

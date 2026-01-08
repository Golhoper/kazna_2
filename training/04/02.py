# @classmethod — это метод, который работает с КЛАССОМ, а не с объектом.
# обычный метод → работает с объектом (self)
# @classmethod → работает с классом (cls)

class User:
    role = "user"

    @classmethod
    def change_role(cls, new_role):
        cls.role = new_role

User.change_role("admin")
print(User.role)

# cls — это сам класс User
# метод меняет общие данные класса
# @classmethod не знает, какой объект ты используешь — он работает со всеми сразу.
# @classmethod получает класс (cls) и работает с ним, а обычный метод работает с объектом (self).

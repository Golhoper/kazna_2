# @staticmethod — это обычная функция, просто лежащая внутри класса.
#	•	не получает self
#	•	не получает cls
#	•	не знает ничего о классе и объекте

# Класс — это папка
# Методы — это файлы внутри папки
#	•	обычный метод → файл, которому нужен объект
#	•	@classmethod → файл, которому нужен класс
#	•	@staticmethod → файл, который просто лежит в папке

class UserValidator:

    @staticmethod
    def is_valid_age(age):
        return age >= 18

if UserValidator.is_valid_age(19):
    print("Можно регистрироваться")
else:
    print("Вы не достигли совершеннолетия")


# @staticmethod не получает ни self, ни cls и не имеет доступа к классу.

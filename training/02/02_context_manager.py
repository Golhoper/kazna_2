import os

# Получаем путь к директории, где находится этот скрипт
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "example.txt")


with open(file_path, "w", encoding="utf-8") as file:
    file.write("Жекичан, шуруй домой")
with open(file_path, "r", encoding="utf-8") as file:
    print(file.read())

import requests
import os

response = requests.get("https://example.com")
if response.status_code==200:
    print(response.status_code)
else:
    print('Ошибка')
print(response.text[:300])

print(response.headers)

# Получаем путь к директории, где находится этот скрипт
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "example_response.html")

with open(file_path, "w", encoding="utf-8") as file:
    file.write(response.text)
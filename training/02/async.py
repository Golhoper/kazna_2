import asyncio
import time

class AsyncCat:
    def __init__(self, name):
        self.name = name
    
    # Обычный синхронный метод
    def meow_sync(self):
        print(f"{self.name}: Мяу!")
        time.sleep(1)  # Блокирует весь поток
        return "Готово"
    
    # Асинхронный метод
    async def meow_async(self):
        print(f"{self.name}: Мяу!")
        await asyncio.sleep(1)  # Не блокирует, позволяет другим задачам работать
        return "Готово асинхронно"

# Использование
async def main():
    cat = AsyncCat("Барсик")
    
    # Синхронный вызов (медленнее)
    print("Синхронный вызов:")
    start = time.time()
    cat.meow_sync()
    cat.meow_sync()
    print(f"Время: {time.time() - start:.2f} сек")
    
    # Асинхронный вызов (быстрее)
    print("\nАсинхронный вызов:")
    start = time.time()
    
    # Создаём задачи (не запускаем их сразу!)
    task1 = asyncio.create_task(cat.meow_async())
    task2 = asyncio.create_task(cat.meow_async())
    
    # Ждём выполнения обеих задач
    await task1
    await task2
    
    print(f"Время: {time.time() - start:.2f} сек")

# Запускаем асинхронную программу
asyncio.run(main())
import asyncio
import httpx

async def get_post(client, post_id):
    response = await client.get(f"https://jsonplaceholder.typicode.com/posts/{post_id}")

    data = response.json()

    print("Post ID:", post_id)
    print("Status:", response.status_code)
    print("Title:", data["title"])
    print("-" * 50)

async def main():
    async with httpx.AsyncClient() as client:
     await get_post(client, 1)
     await get_post(client, 2)
     await get_post(client, 3)
    
asyncio.run(main())

#Как делают в реальных проектах:

#Клиент создают один раз
#Используют много раз
#Закрывают один раз

#Аналогия (очень простая)
#	•	AsyncClient — это браузер
#	•	Запросы — вкладки

#Ты же:
#	•	не открываешь новый браузер для каждого сайта
#	•	ты открываешь вкладки в одном браузере

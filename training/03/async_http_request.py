import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/users")
        users = response.json()
        print(response.status_code)
        print(users[0]["name"])


asyncio.run(main())
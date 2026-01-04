import asyncio
import httpx

async def get_post(post_id):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://jsonplaceholder.typicode.com/posts/{post_id}")

        data = response.json()

        print("Post ID:", post_id)
        print("Status:", response.status_code)
        print("Title:", data["title"])
        print("-" * 50)

async def main():
    await get_post(1)
    await get_post(2)
    await get_post(3)
    
asyncio.run(main())
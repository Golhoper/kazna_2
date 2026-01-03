import requests

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get("https://example.com", headers=headers)

print(response.status_code)
print(response.headers)
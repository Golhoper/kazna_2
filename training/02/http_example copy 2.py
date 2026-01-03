import requests

params = {
    "name": "alex",
    "age": 25
}

response = requests.get("https://httpbin.org/get", params=params)

print(response.status_code)

print(response.url)

print(response.text)
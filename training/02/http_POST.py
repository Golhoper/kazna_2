import requests

payload = {
    "name": "alex",
    "age": 25
}

response = requests.post(" https://httpbin.org/post", json=payload)

print(response.status_code)

print(response.url)

print(response.text)
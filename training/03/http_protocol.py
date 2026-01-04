import requests

response = requests.get("https://jsonplaceholder.typicode.com/users")
users = response.json()
print(response.status_code)
print(users[0]["name"])
print(users[0]["email"])
print(users[4]["website"])


import requests

data = {
    "title": "My first post",
    "body": "Hello REST API",
    "userId": 1,
    "name": "Lexa"
}

response = requests.post("https://jsonplaceholder.typicode.com/posts", json=data)
primer = response.json()
print(response.status_code)
print(primer["name"])
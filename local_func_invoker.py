import requests

url = "http://localhost:8080"

param = {"artists":["bruno mars"], "song":"thats what I like"}

r = requests.post(url, json=param)

print(r.content)

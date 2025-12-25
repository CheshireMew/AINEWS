import urllib.request
import json

url = "http://localhost:8000/api/spiders/run/odaily"
data = {"items": 5}

try:
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except Exception as e:
    print(f"Error: {e}")

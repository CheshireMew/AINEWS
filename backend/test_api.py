import urllib.request
import json
import sys

base = "http://localhost:8000"

def get(url):
    try:
        with urllib.request.urlopen(base + url) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"GET {url} failed: {e}")
        return None

def post(url, data):
    try:
        req = urllib.request.Request(base + url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"POST {url} failed: {e}")
        return None

try:
    print("Testing Root...")
    print("Root:", get("/"))
    
    print("\nTesting Stats...")
    stats = get("/api/stats")
    print("Stats Response:", str(stats)[:100] + "...")
    
    print("\nTesting Login...")
    login = post("/api/login", {"password": "admin123"})
    print("Login:", login)
    
    print("\nTesting News List...")
    news = get("/api/news?limit=2")
    if news and 'data' in news:
        print(f"News Count: {len(news['data'])}")
    else:
        print("News failed")

except Exception as e:
    print(f"Test script error: {e}")

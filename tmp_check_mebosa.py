import requests
import time

start = time.time()
try:
    print("Fetching mebosa...")
    response = requests.get("http://localhost:8000/api/player/mebosa", timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Time: {time.time() - start:.2f}s")
    try:
        print(response.json())
    except:
        print(response.text[:500])
except Exception as e:
    print(f"Error: {e}")
    print(f"Time: {time.time() - start:.2f}s")

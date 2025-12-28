import requests

# Check if SkyHelper has items endpoint
endpoints = [
    "https://api.skyhelper.altpapier.dev/v1/items",
    "https://api.skyhelper.altpapier.dev/v1/items/SHARD_SEER",
    "https://api.skyhelper.altpapier.dev/v1/bazaar/items",
]

for url in endpoints:
    print(f"\nTrying: {url}")
    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'AltSky/1.0'})
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else resp.text[:200]
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:10]}")
            elif isinstance(data, list):
                print(f"  Items count: {len(data)}")
            else:
                print(f"  Response: {data[:200]}")
    except Exception as e:
        print(f"  Error: {e}")

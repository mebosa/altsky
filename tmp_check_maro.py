import requests

# Check maro.skyhelper.kr API or SkyCrypt items endpoint
urls_to_try = [
    "https://sky.shiiiyu.moe/api/v2/items/SHARD_SEER",
    "https://raw.githubusercontent.com/SkyCryptWebsite/SkyCrypt/master/src/constants/items.json",
]

for url in urls_to_try:
    print(f"\nTrying: {url[:60]}...")
    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            text = resp.text[:500]
            print(f"  Content preview: {text}")
    except Exception as e:
        print(f"  Error: {e}")

# Also check SkyCrypt github for attribute shards
print("\n\nChecking SkyCrypt constants for shard textures...")
skycrypt_url = "https://api.github.com/repos/SkyCryptWebsite/SkyCrypt/contents/src/constants"
try:
    resp = requests.get(skycrypt_url, timeout=10)
    if resp.status_code == 200:
        files = [f['name'] for f in resp.json()]
        print(f"Constants files: {files}")
except Exception as e:
    print(f"Error: {e}")

import requests

# Check SkyCrypt's item texture API
SKYCRYPT_ITEMS_URL = "https://sky.shiiyu.moe/api/v2/items"

try:
    resp = requests.get(SKYCRYPT_ITEMS_URL, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        
        # Find SHARD items
        shard_items = {k: v for k, v in data.items() if k.startswith('SHARD_')}
        print(f"Found {len(shard_items)} SHARD_ items in SkyCrypt")
        
        # Print first few with texture info
        for item_id, item_data in list(shard_items.items())[:5]:
            print(f"\n{item_id}:")
            print(f"  name: {item_data.get('name')}")
            print(f"  texture: {item_data.get('texture', 'N/A')[:100] if item_data.get('texture') else 'N/A'}")
            print(f"  material: {item_data.get('material')}")
            if item_data.get('skin'):
                print(f"  HAS SKIN")
    else:
        print(f"SkyCrypt items API returned {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")

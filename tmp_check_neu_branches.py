import requests

# Check different NEU repo paths
base_urls = [
    "https://raw.githubusercontent.com/NotEnoughUpdates/NotEnoughUpdates-REPO/master/items",
    "https://raw.githubusercontent.com/NotEnoughUpdates/NotEnoughUpdates-REPO/prerelease/items",
    "https://raw.githubusercontent.com/NotEnoughUpdates/NotEnoughUpdates-REPO/dangerous/items",
]

test_items = ["SHARD_SEER", "SHARD_VORACIOUS_SPIDER", "SHARD_AERO", "SHARD_BAL"]

for base in base_urls:
    print(f"\nChecking {base.split('/')[-2]}...")
    for item_id in test_items:
        url = f"{base}/{item_id}.json"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                nbttag = data.get('nbttag', '')
                has_skull = 'SkullOwner' in nbttag or 'textures' in nbttag
                print(f"  {item_id}: FOUND, has_skull={has_skull}")
                if has_skull:
                    # Extract texture value
                    import re
                    match = re.search(r'Value:"([^"]+)"', nbttag)
                    if match:
                        print(f"    Texture: {match.group(1)[:50]}...")
        except:
            pass

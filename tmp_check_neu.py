import requests

# Check NEU repo for shard items
NEU_ITEMS_URL = "https://raw.githubusercontent.com/NotEnoughUpdates/NotEnoughUpdates-REPO/master/items"

test_items = ["SHARD_SEER", "SHARD_VORACIOUS_SPIDER", "ENCHANTED_POISONOUS_POTATO"]

for item_id in test_items:
    url = f"{NEU_ITEMS_URL}/{item_id}.json"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n{item_id}:")
            print(f"  displayname: {data.get('displayname')}")
            print(f"  nbttag: {data.get('nbttag', 'N/A')[:200] if data.get('nbttag') else 'N/A'}")
            # Check for skull texture in nbttag
            nbttag = data.get('nbttag', '')
            if 'SkullOwner' in nbttag or 'textures' in nbttag:
                print(f"  HAS SKULL TEXTURE")
        else:
            print(f"\n{item_id}: NOT FOUND in NEU repo (status {resp.status_code})")
    except Exception as e:
        print(f"\n{item_id}: Error - {e}")

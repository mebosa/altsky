import requests
import json

# Check Hypixel Bazaar API for item texture info
resp = requests.get('https://api.hypixel.net/v2/skyblock/bazaar', timeout=15)
data = resp.json()
products = data.get('products', {})

# Check a few SHARD items
for item_id in ['SHARD_SEER', 'SHARD_VORACIOUS_SPIDER', 'ENCHANTED_POISONOUS_POTATO']:
    product = products.get(item_id)
    if product:
        print(f"\n{item_id}:")
        print(json.dumps(product, indent=2)[:1000])
    else:
        print(f"\n{item_id}: NOT FOUND")

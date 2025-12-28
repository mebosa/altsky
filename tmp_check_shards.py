import requests

resp = requests.get('https://api.hypixel.net/resources/skyblock/items', timeout=10)
data = resp.json()
items = data.get('items', [])
shard_items = [i for i in items if i.get('id', '').startswith('SHARD_')]
print(f'Found {len(shard_items)} SHARD_ items in Hypixel items API')
if shard_items:
    print('First 10:')
    for item in shard_items[:10]:
        has_skin = bool(item.get('skin'))
        material = item.get('material', 'N/A')
        print(f"  {item.get('id')}: material={material}, has_skin={has_skin}")

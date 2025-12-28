
import json

with open('backend/tmp/bazaar_allocator_state.json', 'r') as f:
    data = json.load(f)

shards = {}
items = data.get('items', {})
for key in items.keys():
    if key.startswith('SHARD_') or key == 'THUNDER_SHARDS':
        name = key.replace('SHARD_', '').replace('_', ' ').title() + ' Shard'
        if key == 'THUNDER_SHARDS':
            name = 'Thunder Shards'
        shards[key] = {"name": name, "rarity": "RARE"} # Default rarity

print("SHARD_DATA = {")
for k, v in shards.items():
    print(f'    "{k}": {json.dumps(v)},')
print("}")

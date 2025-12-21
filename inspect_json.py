import json

with open('c:/altskydev/altsky/tmp/profile_full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for uid, member in data['members'].items():
    print(f"Member {uid}:")
    if 'inventory' in member:
        print(f"  Inventory keys: {member['inventory'].keys()}")
    else:
        print("  No inventory key")

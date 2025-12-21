import json
import os
import sys
import django
from django.conf import settings

# Configure Django settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DEBUG=True,
    )
    django.setup()

from backend.api.domain.profile_summary import summarize_profile
from backend.api.domain.nbt_parser import extract_equipment_from_profile, extract_accessories_from_profile
from backend.api.views import _serialize_item, _serialize_accessory

def debug_flow():
    # Try to find a profile json
    path = 'c:/altskydev/altsky/tmp/profile_full.json'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'members' in data:
        profile = data
        # uuid = list(profile['members'].keys())[0] # Pick first member
        uuid = '28667672039044989b0019b14a2c34d6'
        if uuid not in profile['members']:
             print(f"UUID {uuid} not found in profile members: {profile['members'].keys()}")
             uuid = list(profile['members'].keys())[0]
        member_data = profile['members'][uuid]
    elif 'profile' in data:
        profile = data['profile']
        uuid = list(profile['members'].keys())[0] # Pick first member
        member_data = profile['members'][uuid]
    else:
        print("Unknown JSON structure")
        return

    print(f"Debugging for UUID: {uuid}")
    
    inventory = member_data.get('inventory', {})
    print(f"Inventory Keys: {inventory.keys()}")
    if 'inv_armor' in inventory:
        print(f"inv_armor type: {type(inventory['inv_armor'])}")
        print(f"inv_armor keys: {inventory['inv_armor'].keys()}")
        print(f"inv_armor data length: {len(inventory['inv_armor'].get('data', ''))}")

    # 1. Summarize Profile (uses accessories.py)
    print("--- Running summarize_profile ---")
    try:
        summary = summarize_profile(uuid, profile)
        acc_summary = summary.get('accessories', {})
        print(f"Summary Accessories Count: {len(acc_summary.get('items', []))}")
        print(f"Selected Power: {acc_summary.get('selected_power')}")
        print(f"Magical Power (Summary): {acc_summary.get('magical_power')}")
    except Exception as e:
        print(f"summarize_profile failed: {e}")
        import traceback
        traceback.print_exc()
        summary = {}

    # 2. NBT Parser Extraction
    print("\n--- Running NBT Parser Extraction ---")
    equipment = extract_equipment_from_profile(member_data)
    print(f"Equipment: {[k for k, v in equipment.items() if v]}")
    
    accessories = extract_accessories_from_profile(member_data)
    print(f"Accessories Count (NBT Parser): {len(accessories)}")
    
    # 3. Construct Payload
    print("\n--- Constructing Payload ---")
    payload = {
        'uuid': uuid,
        'profile_id': profile.get('profile_id'),
        'skyblock_level': summary.get('skyblock_level', {}).get('level', 0)
    }
    
    if any(equipment.values()):
        equipment_payload = {}
        for slot, item in equipment.items():
            if item:
                equipment_payload[slot] = _serialize_item(item)
        payload['equipment'] = equipment_payload
        
    if accessories:
        payload['accessories'] = [_serialize_accessory(item) for item in accessories]
        
    # Add selected power from summary
    if summary and 'accessories' in summary:
        selected_power = summary['accessories'].get('selected_power')
        if selected_power:
            payload['selected_power'] = selected_power

    print(f"Payload Keys: {payload.keys()}")
    if 'equipment' in payload:
        print(f"Payload Equipment: {payload['equipment'].keys()}")
    if 'accessories' in payload:
        print(f"Payload Accessories Count: {len(payload['accessories'])}")
    print(f"Payload Selected Power: {payload.get('selected_power')}")
    
    # Check equipment details
    if 'equipment' in payload:
        boots = payload['equipment'].get('boots')
        if boots:
            print(f"Boots: {boots.get('id')} - Stars: {boots.get('stars')} - Enchants: {len(boots.get('enchants', {}))}")

if __name__ == "__main__":
    debug_flow()

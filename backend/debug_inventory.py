import os
import sys
import requests
import json
from pathlib import Path

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.domain.wardrobe import _parse_inventory_items

def load_env_value(path, key):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            env_key, env_value = line.split('=', 1)
            if env_key == key:
                return env_value
    return None

def main():
    repo_root = Path('c:/altskydev/altsky')
    
    # Use local file instead of API
    profile_path = repo_root / 'tmp' / 'profile_full.json'
    if not profile_path.exists():
        print(f"File not found: {profile_path}")
        return

    print(f"Reading profile from {profile_path}...")
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
            
        # profile_full.json seems to be a single profile object, not the response with 'profiles' list
        # Check if it has 'members' directly
        if 'members' in profile_data:
            members = profile_data['members']
        else:
            # Maybe it's the response format
            if 'profiles' in profile_data:
                members = profile_data['profiles'][0]['members']
            else:
                print("Could not find members in profile data")
                return

        # Pick the first member
        uuid = list(members.keys())[0]
        member = members[uuid]
        print(f"Analyzing member: {uuid}")
        
        inventory = member.get('inventory', {})
        inv_contents = inventory.get('inv_contents')
        
        if not inv_contents:
            print("No inventory contents found")
            return

        print("Parsing inventory...")
        items = _parse_inventory_items(inv_contents)
        
        stone_count = 0
        skyblock_menu_count = 0
        
        for i, item in enumerate(items):
            if item is None:
                continue
                
            item_id = item.get('id')
            name = item.get('name')
            mc_id = item.get('mc_id')
            
            if item_id == '1' or item_id == 'minecraft:stone' or mc_id == '1' or mc_id == 'minecraft:stone':
                print(f"Slot {i}: Found Stone! Name: {name}, ID: {item_id}, MC_ID: {mc_id}")
                stone_count += 1
            
            if 'SkyBlock Menu' in name:
                print(f"Slot {i}: Found SkyBlock Menu! Name: {name}, ID: {item_id}, MC_ID: {mc_id}")
                skyblock_menu_count += 1
                
        print(f"Total Stones: {stone_count}")
        print(f"Total SkyBlock Menus: {skyblock_menu_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

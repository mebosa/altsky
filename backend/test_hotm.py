"""Test HOTM extraction"""
import requests
import json
from pathlib import Path


def load_env_value(path, key):
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


repo_root = Path('c:/altskydev/altsky')
api_key = load_env_value(repo_root / 'backend' / '.env', 'HYPIXEL_API_KEY')
if not api_key:
    raise SystemExit('API key not found')

# Test with a player that should have HOTM data
# Using Refraction as example - well-known SkyBlock player
username = 'Refraction'

print(f"Looking up player: {username}")
mojang_resp = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{username}', timeout=10)
mojang_resp.raise_for_status()
uuid = mojang_resp.json()['id']
print(f"UUID: {uuid}")

profiles_resp = requests.get('https://api.hypixel.net/v2/skyblock/profiles', params={'key': api_key, 'uuid': uuid}, timeout=10)
profiles_resp.raise_for_status()

profiles = profiles_resp.json()['profiles']
print(f"\nFound {len(profiles)} profiles")

# Find the active profile
for p in profiles:
    pid = p['profile_id']
    cute_name = p.get('cute_name', 'Unknown')
    member = p['members'][uuid]
    
    # Check for mining_core
    mining_core = member.get('mining_core', {})
    if mining_core:
        tier = mining_core.get('tier', 0)
        experience = mining_core.get('experience', 0)
        nodes = mining_core.get('nodes', {})
        print(f"\nProfile: {cute_name}")
        print(f"  HOTM Tier: {tier}")
        print(f"  Experience: {experience}")
        print(f"  Perks count: {len([k for k in nodes.keys() if not k.startswith('toggle_')])}")
        print(f"  Powder Mithril: {mining_core.get('powder_mithril', 0)}")
        print(f"  Powder Gemstone: {mining_core.get('powder_gemstone', 0)}")
        print(f"  Powder Glacite: {mining_core.get('powder_glacite', 0)}")
        
        # Test extraction
        from api.domain.nbt_parser import extract_hotm_from_profile
        hotm = extract_hotm_from_profile(member)
        
        if hotm:
            print(f"\n✅ Extracted HOTM data successfully:")
            print(f"  Tier: {hotm['tier']}")
            print(f"  Experience: {hotm['experience']}")
            print(f"  Perks: {len(hotm['perks'])} perks")
            print(f"  Tokens spent: {hotm.get('tokens_spent', 0)}")
            print(f"  Selected ability: {hotm.get('selected_ability', 'None')}")
            
            # Save for inspection
            with open('c:/altskydev/altsky/tmp/hotm_test.json', 'w', encoding='utf-8') as f:
                json.dump(hotm, f, indent=2)
            print(f"\n💾 Saved to tmp/hotm_test.json")
        else:
            print(f"\n❌ Failed to extract HOTM data (returned None)")
        
        break
else:
    print("\n⚠️  No profile found with mining_core data")

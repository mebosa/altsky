"""Check HOTM data directly from Hypixel API"""
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

uuid = 'a04a9f0510e347a7a2d200b4754672c7'  # highly_soft

print(f"Fetching profiles for {uuid}...")
try:
    profiles_resp = requests.get(
        'https://api.hypixel.net/v2/skyblock/profiles',
        params={'key': api_key, 'uuid': uuid},
        timeout=15
    )
    profiles_resp.raise_for_status()
    
    profiles = profiles_resp.json().get('profiles', [])
    print(f"Found {len(profiles)} profiles\n")
    
    for profile in profiles:
        cute_name = profile.get('cute_name', 'Unknown')
        game_mode = profile.get('game_mode')
        members = profile.get('members', {})
        member = members.get(uuid, {})
        
        mining_core = member.get('mining_core', {})
        
        if mining_core:
            tier = mining_core.get('tier', 0)
            exp = mining_core.get('experience', 0)
            nodes = mining_core.get('nodes', {})
            perk_count = len([k for k in nodes.keys() if not k.startswith('toggle_')])
            
            print(f"Profile: {cute_name} (mode: {game_mode or 'normal'})")
            print(f"  ✅ Has mining_core!")
            print(f"  Tier: {tier}")
            print(f"  Experience: {exp}")
            print(f"  Perks: {perk_count}")
            print(f"  Powder - Mithril: {mining_core.get('powder_mithril', 0)}")
            print(f"  Powder - Gemstone: {mining_core.get('powder_gemstone', 0)}")
            print(f"  Powder - Glacite: {mining_core.get('powder_glacite', 0)}")
            print()
        else:
            print(f"Profile: {cute_name} (mode: {game_mode or 'normal'})")
            print(f"  ❌ No mining_core data")
            print()
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

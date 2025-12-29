"""Debug HOTM extraction for highly_soft"""
import requests
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from api.domain.nbt_parser import extract_hotm_from_profile


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

print(f"Fetching profiles for highly_soft...")
profiles_resp = requests.get(
    'https://api.hypixel.net/v2/skyblock/profiles',
    params={'key': api_key, 'uuid': uuid},
    timeout=15
)
profiles_resp.raise_for_status()

profiles = profiles_resp.json().get('profiles', [])

for profile in profiles:
    cute_name = profile.get('cute_name', 'Unknown')
    members = profile.get('members', {})
    member = members.get(uuid, {})
    
    mining_core = member.get('mining_core', {})
    
    if not mining_core:
        print(f"\n{cute_name}: No mining_core")
        continue
    
    print(f"\n{'='*60}")
    print(f"Profile: {cute_name}")
    print(f"{'='*60}")
    
    # Show raw mining_core structure
    print("\nRaw mining_core keys:")
    for key in sorted(mining_core.keys()):
        value = mining_core[key]
        if isinstance(value, dict):
            print(f"  {key}: <dict with {len(value)} keys>")
        elif isinstance(value, list):
            print(f"  {key}: <list with {len(value)} items>")
        else:
            print(f"  {key}: {value}")
    
    # Test extraction
    print("\nTesting extract_hotm_from_profile()...")
    hotm = extract_hotm_from_profile(member)
    
    if hotm:
        print("✅ Extraction succeeded:")
        print(f"  Tier: {hotm['tier']}")
        print(f"  Experience: {hotm['experience']}")
        print(f"  Perks: {len(hotm['perks'])}")
        print(f"  Tokens spent: {hotm.get('tokens_spent', 0)}")
    else:
        print("❌ Extraction returned None")
        print(f"  Reason: tier = {mining_core.get('tier', 0)} (must be > 0)")
    
    # Save for inspection
    output_file = f'c:/altskydev/altsky/tmp/mining_core_{cute_name.lower()}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mining_core, f, indent=2)
    print(f"\n💾 Saved raw mining_core to: {output_file}")

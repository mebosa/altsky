import requests
from pathlib import Path
import json


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

username = 'Refraction'
mojang_resp = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{username}', timeout=10)
mojang_resp.raise_for_status()
uuid = mojang_resp.json()['id']
profiles_resp = requests.get('https://api.hypixel.net/v2/skyblock/profiles', params={'key': api_key, 'uuid': uuid}, timeout=10)
profiles_resp.raise_for_status()

profiles = profiles_resp.json()['profiles']
print(f"Found {len(profiles)} profiles")

best_profile = None
max_last_save = 0

for p in profiles:
    pid = p['profile_id']
    cute_name = p.get('cute_name', 'Unknown')
    member = p['members'][uuid]
    last_save = member.get('last_save', 0)
    inv = member.get('inventory', {})
    inv_len = len(inv)
    print(f"Profile {cute_name} ({pid}): Last Save {last_save}, Inventory Keys: {inv_len}")
    
    if inv_len > 0:
        best_profile = p
        break

if best_profile:
    print(f"Saving profile: {best_profile.get('cute_name')}")
    with open('c:/altskydev/altsky/tmp/profile_full.json', 'w', encoding='utf-8') as f:
        json.dump(best_profile, f, indent=2)
else:
    print("No suitable profile found")

# profile = profiles_resp.json()['profiles'][0]
# member = profile['members'][uuid]

bank_account = member.get('profile', {}).get('bank_account')
print('bank_account:', json.dumps(bank_account, indent=2) if isinstance(bank_account, dict) else bank_account)

personal_bank = member.get('personal_bank')
print('personal_bank:', json.dumps(personal_bank, indent=2) if isinstance(personal_bank, dict) else personal_bank)

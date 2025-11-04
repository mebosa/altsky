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

username = 'Taegi88'
mojang_resp = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{username}', timeout=10)
mojang_resp.raise_for_status()
uuid = mojang_resp.json()['id']
profiles_resp = requests.get('https://api.hypixel.net/v2/skyblock/profiles', params={'key': api_key, 'uuid': uuid}, timeout=10)
profiles_resp.raise_for_status()
profile = profiles_resp.json()['profiles'][0]
member = profile['members'][uuid]

bank_account = member.get('profile', {}).get('bank_account')
print('bank_account:', json.dumps(bank_account, indent=2) if isinstance(bank_account, dict) else bank_account)

personal_bank = member.get('personal_bank')
print('personal_bank:', json.dumps(personal_bank, indent=2) if isinstance(personal_bank, dict) else personal_bank)

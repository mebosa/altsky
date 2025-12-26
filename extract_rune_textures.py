import requests
import base64
import json
import urllib.parse
import re

# Get list of all rune files from NEU repo
print("Fetching rune file list...")
r = requests.get('https://api.github.com/repos/NotEnoughUpdates/NotEnoughUpdates-REPO/contents/items')
all_files = r.json()
rune_files = [f['name'] for f in all_files if '_RUNE;' in f['name']]

print(f"Found {len(rune_files)} rune files")

rune_textures = {}

for filename in rune_files:
    try:
        url = f"https://raw.githubusercontent.com/NotEnoughUpdates/NotEnoughUpdates-REPO/master/items/{urllib.parse.quote(filename)}"
        r = requests.get(url, timeout=10)
        data = r.json()
        nbttag = data.get('nbttag', '')
        
        # Extract texture value from nbttag
        match = re.search(r'Value:"([^"]+)"', nbttag)
        if match:
            texture_b64 = match.group(1)
            decoded = base64.b64decode(texture_b64).decode('utf-8')
            texture_data = json.loads(decoded)
            skin_url = texture_data.get('textures', {}).get('SKIN', {}).get('url', '')
            if skin_url:
                texture_hash = skin_url.rsplit('/', 1)[-1]
                # Extract rune name (e.g., BITE from BITE_RUNE;1.json)
                rune_name = filename.split('_RUNE')[0]
                if rune_name not in rune_textures:
                    rune_textures[rune_name] = texture_hash
                    print(f'    "{rune_name}": "{texture_hash}",')
    except Exception as e:
        print(f"Error with {filename}: {e}")

print("\n\nFinal mapping:")
print("RUNE_TEXTURES = {")
for name, hash in sorted(rune_textures.items()):
    print(f'    "{name}": "{hash}",')
print("}")

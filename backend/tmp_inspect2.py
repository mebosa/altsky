import requests, base64, gzip, json, nbtlib, io
name = "nbskd"
mojang = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{name}", timeout=10)
mojang.raise_for_status()
uuid = mojang.json()["id"]
headers = {'API-Key': "10b0150e-5b1b-4861-9b7b-d3e00cab6ea5"}
resp = requests.get("https://api.hypixel.net/v2/skyblock/profiles", params={'uuid': uuid}, headers=headers, timeout=20)
resp.raise_for_status()
member = resp.json()['profiles'][0]['members'][uuid]
wardrobe = member['inventory']['wardrobe_contents']
raw = base64.b64decode(wardrobe['data'])
try:
    payload = gzip.decompress(raw)
except OSError:
    import zlib
    payload = zlib.decompress(raw)
nbt = nbtlib.File.parse(io.BytesIO(payload))
for idx, comp in enumerate(nbt['i'][:10]):
    if not comp:
        continue
    print('slot', idx)
    print('id', comp.get('id'))
    print('Count', comp.get('Count'))
    tag = comp.get('tag')
    if tag:
        print('tag keys', list(tag.keys()))
        skull = tag.get('SkullOwner')
        if skull:
            props = skull.get('Properties')
            if props:
                tex = props.get('textures')
                if tex:
                    tex_val = tex[0].get('Value')
                    print('texture len', len(str(tex_val)))
                    print('texture sample', str(tex_val)[:60])
    extra = tag.get('ExtraAttributes') if tag else None
    if extra:
        print('extra keys', list(extra.keys())[:5])
    print('-'*40)

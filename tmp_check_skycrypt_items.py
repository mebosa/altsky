import requests

# Check SkyCrypt items.js for shard textures
items_url = "https://raw.githubusercontent.com/SkyCryptWebsite/SkyCrypt/master/src/constants/items.js"
resp = requests.get(items_url, timeout=15)
if resp.status_code == 200:
    content = resp.text
    print(f"Total length: {len(content)}")
    
    # Find SHARD_ related entries
    lines = content.split('\n')
    shard_lines = []
    for i, line in enumerate(lines):
        if 'SHARD_' in line or 'shard_' in line.lower():
            context = lines[max(0, i-1):min(len(lines), i+3)]
            shard_lines.append((i, '\n'.join(context)))
    
    print(f"\nFound {len(shard_lines)} lines with SHARD:")
    for line_num, context in shard_lines[:10]:
        print(f"\n--- Line {line_num} ---")
        print(context)
else:
    print(f"Failed: {resp.status_code}")

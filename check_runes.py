import requests
import base64
import json
import re

# Get SkyCrypt's items data
url = 'https://raw.githubusercontent.com/SkyCryptWebsite/SkyCrypt/master/src/constants/items.js'
r = requests.get(url, timeout=10)
print("Status:", r.status_code)

# Search for rune-related content
text = r.text
lines = text.split('\n')
for i, line in enumerate(lines):
    if 'rune' in line.lower() or 'RUNE' in line:
        print(f"Line {i}: {line[:150]}")

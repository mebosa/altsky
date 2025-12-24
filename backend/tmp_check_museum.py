#!/usr/bin/env python
"""Check museum API data structure"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

import requests
from api.domain.museum import parse_museum

# Fetch museum data from backend with force_refresh
response = requests.get('http://localhost:8000/api/hypixel/profile-by-name/mebosa/84473185-b58a-4bc1-8801-ad24110b5db1?force_refresh=1')
if response.status_code == 200:
    data = response.json()
    print(f"✓ Networth type: {type(data['networth'])}")
    print(f"✓ Networth total: {data['networth']['total']/1e9:.2f}B")
    print(f"✓ Museum value (Hypixel base): {data['museum']['value']/1e9:.2f}B")
    print(f"✓ Museum items count: {len(data['museum']['items'])}")
    print(f"✓ Networth categories: {list(data['networth']['categories'].keys())}")
    print(f"✓ Networth categories museum total: {data['networth']['categories'].get('museum', {}).get('total', 'NOT_SET')}")
    
    # Check if museum was added to networth or not
    expected_with_museum = data['networth']['total'] + data['museum']['value']
    print(f"\n--- Analysis ---")
    print(f"Current networth: {data['networth']['total']/1e9:.2f}B")
    print(f"Museum base value: {data['museum']['value']/1e9:.2f}B")
    print(f"Expected if museum added: {expected_with_museum/1e9:.2f}B")
    print(f"Museum IS{'IN' if data['networth']['categories']['museum']['total'] > 0 else ' NOT'} included in networth")
else:
    print(f"✗ Failed: {response.status_code}")


import requests
import json
import os

def update_items():
    print("Downloading Hypixel items...")
    try:
        response = requests.get('https://api.hypixel.net/resources/skyblock/items')
        response.raise_for_status()
        data = response.json()
        
        if not data.get('success'):
            print("Failed to fetch items: API returned success=false")
            return

        items = data.get('items', [])
        print(f"Downloaded {len(items)} items.")
        
        with open('backend/hypixel_items.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print("Saved to backend/hypixel_items.json")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_items()

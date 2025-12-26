import requests
import json

URL = "http://localhost:8000/api/hypixel/profile/84473185b58a4bc18801ad24110b5db1/84473185-b58a-4bc1-8801-ad24110b5db1?weapon_slot=0"

def debug_request():
    print(f"Requesting {URL}...")
    try:
        response = requests.get(URL, timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response OK")
            
            # Check computed stats
            stats = data.get('computed_stats', {}).get('stats', {})
            print(f"Computed Stats: {stats}")
            
            # Check breakdown for damage/strength
            breakdown = data.get('stat_breakdown', {})
            if 'damage' in breakdown:
                print("Damage Breakdown:")
                for bonus in breakdown['damage'].get('bonuses', []):
                    print(f"  - {bonus['source']}: {bonus['value']}")
            
            if 'strength' in breakdown:
                print("Strength Breakdown:")
                for bonus in breakdown['strength'].get('bonuses', []):
                    print(f"  - {bonus['source']}: {bonus['value']}")
                    
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    debug_request()

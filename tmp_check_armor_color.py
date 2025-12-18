import requests
import json

def check_profile():
    # Need UUID for mebosa first
    try:
        print("Fetching player UUID...")
        p_res = requests.get("http://localhost:8000/api/player/mebosa")
        p_res.raise_for_status()
        p_data = p_res.json()
        uuid = p_data.get('uuid')
        print(f"UUID: {uuid}")
        
        url = f"http://localhost:8000/api/hypixel/profile/{uuid}/84473185-b58a-4bc1-8801-ad24110b5db1"
        print(f"Fetching {url}...")
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        
        wardrobe = data.get('wardrobe', {})
        equipped = wardrobe.get('equipped_items', [])
        
        print("Equipped Armor:")
        for i, item in enumerate(equipped):
            if item:
                print(f"Slot {i}: {item.get('id')} | Color: {item.get('leather_color')} | Name: {item.get('name')}")
            else:
                print(f"Slot {i}: Empty")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_profile()

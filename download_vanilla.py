import requests
import os

# Base URL for vanilla textures
base_url = "https://mcasset.cloud/1.20.4/assets/minecraft/textures"

# Items to download
items = {
    "paper": "item/paper.png",
    "jungle_log": "block/jungle_log.png",
    "stone_button": "block/stone_button.png", # stone_button is a block texture usually? No, item model uses block texture.
    # Actually stone_button item texture might be different or just the block texture.
    # Let's check mcasset.cloud structure.
    # usually item/stone_button.png doesn't exist, it uses block/stone_button.png
    "barrier": "item/barrier.png",
    "ghast_tear": "item/ghast_tear.png",
    "prismarine_shard": "item/prismarine_shard.png", # For default shards
}

output_dir = "frontend/static/items/vanilla"
os.makedirs(output_dir, exist_ok=True)

for name, path in items.items():
    url = f"{base_url}/{path}"
    # Try item/ first, then block/ if needed
    
    print(f"Downloading {name} from {url}...")
    try:
        response = requests.get(url)
        if response.status_code == 404:
            # Try block if item failed
            if path.startswith("item/"):
                alt_path = path.replace("item/", "block/")
                url = f"{base_url}/{alt_path}"
                print(f"Retrying with {url}...")
                response = requests.get(url)
        
        response.raise_for_status()
        
        with open(f"{output_dir}/{name}.png", 'wb') as f:
            f.write(response.content)
        print(f"Saved {name}.png")
    except Exception as e:
        print(f"Failed to download {name}: {e}")

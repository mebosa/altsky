import requests
import os

url = "https://mcasset.cloud/1.20.4/assets/minecraft/textures/item/enchanted_book.png"
output_path = "frontend/static/items/enchanted_book.png"

os.makedirs(os.path.dirname(output_path), exist_ok=True)

try:
    response = requests.get(url)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        f.write(response.content)
    print(f"Successfully downloaded {output_path}")
except Exception as e:
    print(f"Failed to download: {e}")

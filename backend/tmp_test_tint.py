import requests
from io import BytesIO
from PIL import Image

def test_tint(layer):
    url = f"https://cdn.jsdelivr.net/gh/InventivetalentDev/minecraft-assets@1.8.9/assets/minecraft/textures/models/armor/leather_layer_{layer}.png"
    print(f"Fetching {url}...")
    res = requests.get(url)
    if res.status_code != 200:
        print(f"Failed to fetch layer {layer}: {res.status_code}")
        return

    try:
        img_data = BytesIO(res.content)
        img = Image.open(img_data).convert("RGBA")
        print(f"Layer {layer} mode: {img.mode}, size: {img.size}")
        
        color_hex = "FF0000" # Red
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)
        
        r_chan, g_chan, b_chan, a_chan = img.split()
        
        r_chan = r_chan.point(lambda i: (i * r) // 255)
        g_chan = g_chan.point(lambda i: (i * g) // 255)
        b_chan = b_chan.point(lambda i: (i * b) // 255)
        
        img = Image.merge("RGBA", (r_chan, g_chan, b_chan, a_chan))
        print(f"Layer {layer} tinted successfully.")
    except Exception as e:
        print(f"Layer {layer} failed to tint: {e}")

test_tint(1)
test_tint(2)

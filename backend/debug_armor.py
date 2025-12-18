import requests
from io import BytesIO
from PIL import Image

def check_armor_color():
    # Remove force=1 to test cache
    url = "http://localhost:8000/api/texture/vanilla-armor/leather/1?color=c83200"
    print(f"Fetching {url}...")
    try:
        res = requests.get(url)
        if res.status_code != 200:
            print(f"Error: Status {res.status_code}")
            print(res.text)
            return

        img = Image.open(BytesIO(res.content))
        print(f"Image mode: {img.mode}, Size: {img.size}")
        
        # Sample a pixel that should be colored (e.g., the chest area)
        # In 64x32 texture:
        # Hat: 0-32, 0-16 (Overlay)
        # Head: 0-32, 16-32 (Base) -> Wait, standard skin layout is different.
        # Armor layout 1.8:
        # Leather helmet is at top left.
        # Let's sample a few non-transparent pixels.
        
        pixels = img.load()
        width, height = img.size
        
        found_color = False
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a > 0: # Non-transparent
                    # Check if it's white-ish or red-ish
                    # Expected color is roughly R=200, G=50, B=0
                    print(f"Pixel at ({x}, {y}): R={r}, G={g}, B={b}, A={a}")
                    if r > 150 and g < 100:
                        print("SUCCESS: Found reddish pixel!")
                        found_color = True
                    elif r > 200 and g > 200 and b > 200:
                        print("FAILURE: Found white pixel!")
                    
                    # Just sample the first few non-transparent ones
                    if found_color: break
            if found_color: break
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_armor_color()

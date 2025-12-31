import json

def find_garden_keys(data, path=""):
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}" if path else key
            if "jacob" in key.lower():
                print(f"Found key: {new_path}")
            find_garden_keys(value, new_path)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            find_garden_keys(item, f"{path}[{i}]")

try:
    with open("tmp/profile_full.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        find_garden_keys(data)
except Exception as e:
    print(f"Error: {e}")

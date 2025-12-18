import os
import json
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# backend/build_armor_cache.py -> backend -> root -> furfsky_temp
FURF_SKY_TEMP_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "furfsky_temp"))
ARMOR_BASE_PATH = os.path.join(FURF_SKY_TEMP_PATH, "assets", "minecraft", "mcpatcher", "cit", "equipment", "armor")
OUTPUT_FILE = os.path.join(BASE_DIR, "api", "domain", "armor_cache.json")

def resolve_texture_path(root_dir, texture_name):
    if not texture_name:
        return None
    
    if not texture_name.endswith('.png'):
        texture_name += '.png'
        
    # Check in current dir
    path = os.path.join(root_dir, texture_name)
    if os.path.exists(path):
        return os.path.relpath(path, FURF_SKY_TEMP_PATH).replace("\\", "/")
        
    # Recursive search in root_dir
    for r, d, f in os.walk(root_dir):
        if texture_name in f:
            return os.path.relpath(os.path.join(r, texture_name), FURF_SKY_TEMP_PATH).replace("\\", "/")
            
    return None

def build_cache():
    LOGGER.info(f"Scanning {ARMOR_BASE_PATH}...")
    cache = {}
    
    if not os.path.exists(ARMOR_BASE_PATH):
        LOGGER.error(f"Path not found: {ARMOR_BASE_PATH}")
        return

    count = 0
    for root, dirs, files in os.walk(ARMOR_BASE_PATH):
        for file in files:
            if file.endswith(".properties"):
                prop_path = os.path.join(root, file)
                try:
                    process_properties_file(prop_path, root, cache)
                    count += 1
                except Exception as e:
                    LOGGER.error(f"Error processing {prop_path}: {e}")
    
    LOGGER.info(f"Processed {count} properties files. Found {len(cache)} items.")
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
    LOGGER.info(f"Saved cache to {OUTPUT_FILE}")

def process_properties_file(prop_path, root_dir, cache):
    ids = []
    layer_1 = None
    layer_2 = None
    
    with open(prop_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '=' not in line:
                continue
                
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            if key == 'nbt.ExtraAttributes.id':
                if value.startswith('regex:'):
                    pattern = value[6:]
                    match = re.match(r'([A-Z0-9_]+)\((.+)\)', pattern)
                    if match:
                        base = match.group(1)
                        suffixes = match.group(2).split('|')
                        for suffix in suffixes:
                            ids.append(f"{base}{suffix}")
                    else:
                        ids.append(pattern)
                elif value.startswith('ipattern:'):
                     pass
                else:
                    ids.append(value)
            
            if key.endswith('layer_1'):
                layer_1 = value
            elif key.endswith('layer_2'):
                layer_2 = value

    if ids and (layer_1 or layer_2):
        l1_path = resolve_texture_path(root_dir, layer_1) if layer_1 else None
        l2_path = resolve_texture_path(root_dir, layer_2) if layer_2 else None
        
        for item_id in ids:
            cache[item_id] = [l1_path, l2_path]

if __name__ == "__main__":
    build_cache()

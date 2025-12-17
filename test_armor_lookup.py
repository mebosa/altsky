import os
import logging
from typing import Dict, Optional, Tuple

# Mocking the path and logger for standalone testing
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Adjust this path to match the container structure or local structure for testing
# In the container, it is /app/furfsky_temp
# Locally it is c:\altskydev\altsky\furfsky_temp
FURF_SKY_TEMP_PATH = r"c:\altskydev\altsky\furfsky_temp"

ARMOR_BASE_PATH = os.path.join(
    FURF_SKY_TEMP_PATH, "assets", "minecraft", "mcpatcher", "cit", "equipment", "armor"
)

_ARMOR_TEXTURE_CACHE: Dict[str, Tuple[Optional[str], Optional[str]]] = {}

def initialize_armor_cache():
    print(f"Initializing armor texture cache from {ARMOR_BASE_PATH}")
    
    if not os.path.exists(ARMOR_BASE_PATH):
        print(f"Armor path not found: {ARMOR_BASE_PATH}")
        return

    count = 0
    for root, dirs, files in os.walk(ARMOR_BASE_PATH):
        for file in files:
            if file.endswith(".properties"):
                prop_path = os.path.join(root, file)
                try:
                    process_properties_file(prop_path, root)
                    count += 1
                except Exception as e:
                    print(f"Error processing {prop_path}: {e}")
    
    print(f"Initialized armor cache with {len(_ARMOR_TEXTURE_CACHE)} items")

def process_properties_file(prop_path: str, root_dir: str):
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
                    # Simple regex handling for common patterns like SUPERIOR_DRAGON_(CHESTPLATE|LEGGINGS|BOOTS)
                    import re
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
            _ARMOR_TEXTURE_CACHE[item_id] = (l1_path, l2_path)

def resolve_texture_path(root_dir: str, texture_name: str) -> Optional[str]:
    if not texture_name:
        return None
    
    if not texture_name.endswith('.png'):
        texture_name += '.png'
        
    path = os.path.join(root_dir, texture_name)
    if os.path.exists(path):
        return path
        
    for r, d, f in os.walk(root_dir):
        if texture_name in f:
            return os.path.join(r, texture_name)
            
    return None

def get_armor_textures(item_id: str):
    if not _ARMOR_TEXTURE_CACHE:
        initialize_armor_cache()
    
    # Logic from the file
    result = _ARMOR_TEXTURE_CACHE.get(item_id)
    if result:
        return result
        
    # Try with/without ARMOR_OF_ prefix
    if item_id.startswith("ARMOR_OF_"):
        alt_id = item_id.replace("ARMOR_OF_", "")
        if alt_id in _ARMOR_TEXTURE_CACHE:
             return _ARMOR_TEXTURE_CACHE[alt_id]
    else:
        alt_id = "ARMOR_OF_" + item_id
        if alt_id in _ARMOR_TEXTURE_CACHE:
             return _ARMOR_TEXTURE_CACHE[alt_id]
             
    return (None, None)

if __name__ == "__main__":
    initialize_armor_cache()
    
    test_ids = [
        "YOG_HELMET",
        "ARMOR_OF_YOG_HELMET",
        "JADED_YOG_HELMET",
        "DIMENSIONAL_YOG_CHESTPLATE",
        "SUPERIOR_DRAGON_CHESTPLATE"
    ]
    
    for tid in test_ids:
        print(f"Testing {tid}: {get_armor_textures(tid)}")

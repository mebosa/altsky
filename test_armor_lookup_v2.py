import os
import logging
from typing import Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

FURF_SKY_TEMP_PATH = r"c:\altskydev\altsky\furfsky_temp"

ARMOR_BASE_PATH = os.path.join(
    FURF_SKY_TEMP_PATH, "assets", "minecraft", "mcpatcher", "cit", "equipment", "armor"
)

_ARMOR_TEXTURE_CACHE: Dict[str, Tuple[Optional[str], Optional[str]]] = {}

def initialize_armor_cache():
    if not os.path.exists(ARMOR_BASE_PATH):
        return

    for root, dirs, files in os.walk(ARMOR_BASE_PATH):
        for file in files:
            if file.endswith(".properties"):
                prop_path = os.path.join(root, file)
                try:
                    process_properties_file(prop_path, root)
                except Exception:
                    pass

def process_properties_file(prop_path: str, root_dir: str):
    ids = []
    layer_1 = None
    layer_2 = None
    
    with open(prop_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            if key == 'nbt.ExtraAttributes.id':
                if value.startswith('regex:'):
                    pattern = value[6:]
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
    if not texture_name: return None
    if not texture_name.endswith('.png'): texture_name += '.png'
    path = os.path.join(root_dir, texture_name)
    if os.path.exists(path): return path
    for r, d, f in os.walk(root_dir):
        if texture_name in f: return os.path.join(r, texture_name)
    return None

def get_armor_textures(item_id: str):
    if not _ARMOR_TEXTURE_CACHE:
        initialize_armor_cache()
    
    REFORGES = [
        "ANCIENT", "WISE", "NECROTIC", "LOVING", "RIDICULOUS", "GIANT", "SUBMERGED", 
        "JADED", "DIMENSIONAL", "RENOWNED", "SPIKED", "HYPER", "REINFORCED", "PERFECT", 
        "HEAVY", "LIGHT", "MYTHIC", "PURE", "FIERCE", "SMART", "TITANIC", "CLEAN", 
        "CUBISM", "BUSTLING", "MOSSY", "FESTIVE", "GLACIAL", "GLOSSY", "STRENGTHENED", 
        "WAXED", "FORTIFIED"
    ]
    
    candidates = [item_id]
    if item_id.startswith("ARMOR_OF_"):
        candidates.append(item_id.replace("ARMOR_OF_", ""))
    else:
        candidates.append("ARMOR_OF_" + item_id)
        
    for reforge in REFORGES:
        if item_id.startswith(f"{reforge}_"):
            stripped = item_id[len(reforge)+1:]
            candidates.append(stripped)
            if stripped.startswith("ARMOR_OF_"):
                candidates.append(stripped.replace("ARMOR_OF_", ""))
            else:
                candidates.append("ARMOR_OF_" + stripped)
    
    for candidate in candidates:
        if candidate in _ARMOR_TEXTURE_CACHE:
             return _ARMOR_TEXTURE_CACHE[candidate]
             
    return (None, None)

if __name__ == "__main__":
    initialize_armor_cache()
    print(f"JADED_YOG_HELMET: {get_armor_textures('JADED_YOG_HELMET')}")
    print(f"DIMENSIONAL_YOG_CHESTPLATE: {get_armor_textures('DIMENSIONAL_YOG_CHESTPLATE')}")

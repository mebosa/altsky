import os
import re
import logging
from typing import Dict, Optional, Tuple

LOGGER = logging.getLogger(__name__)

# Path to furfsky_temp (relative to this file)
# backend/api/domain/armor_textures.py -> backend/api/domain -> backend/api -> backend -> root -> furfsky_temp
FURF_SKY_TEMP_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "furfsky_temp")
)

ARMOR_BASE_PATH = os.path.join(
    FURF_SKY_TEMP_PATH, "assets", "minecraft", "mcpatcher", "cit", "equipment", "armor"
)

# Cache for item_id -> (layer_1_path, layer_2_path)
_ARMOR_TEXTURE_CACHE: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
_CACHE_INITIALIZED = False

def initialize_armor_cache():
    global _CACHE_INITIALIZED
    if _CACHE_INITIALIZED:
        return

    LOGGER.info(f"Initializing armor texture cache from {ARMOR_BASE_PATH}")
    
    if not os.path.exists(ARMOR_BASE_PATH):
        LOGGER.warning(f"Armor path not found: {ARMOR_BASE_PATH}")
        _CACHE_INITIALIZED = True
        return

    count = 0
    # Walk through all directories in armor folder
    for root, dirs, files in os.walk(ARMOR_BASE_PATH):
        for file in files:
            if file.endswith(".properties"):
                prop_path = os.path.join(root, file)
                try:
                    process_properties_file(prop_path, root)
                    count += 1
                except Exception as e:
                    LOGGER.error(f"Error processing {prop_path}: {e}")
    
    LOGGER.info(f"Initialized armor cache with {len(_ARMOR_TEXTURE_CACHE)} items")
    _CACHE_INITIALIZED = True

def process_properties_file(prop_path: str, root_dir: str):
    """
    Parses a .properties file to find the item ID mapping and texture files.
    """
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
            
            # Check for ID mapping
            # nbt.ExtraAttributes.id=regex:SUPERIOR_DRAGON_(CHESTPLATE|LEGGINGS|BOOTS)
            # or nbt.ExtraAttributes.id=SUPERIOR_DRAGON_CHESTPLATE
            if key == 'nbt.ExtraAttributes.id':
                if value.startswith('regex:'):
                    pattern = value[6:]
                    # We can't easily expand regex to all IDs, but we can store the regex?
                    # For now, let's try to extract the base name if possible, or just handle specific common regexes.
                    # Many are like: SUPERIOR_DRAGON_(CHESTPLATE|LEGGINGS|BOOTS)
                    # We can expand this manually.
                    match = re.match(r'([A-Z0-9_]+)\((.+)\)', pattern)
                    if match:
                        base = match.group(1)
                        suffixes = match.group(2).split('|')
                        for suffix in suffixes:
                            ids.append(f"{base}{suffix}")
                    else:
                        # Simple regex or complex one?
                        # If it's just a string without regex chars, treat as ID
                        ids.append(pattern)
                elif value.startswith('ipattern:'):
                     # ipattern is wildcard, harder to map to specific ID
                     pass
                else:
                    ids.append(value)
            
            # Check for textures
            # texture.leather_layer_1=superior_dragon_layer_1
            if key.endswith('layer_1'):
                layer_1 = value
            elif key.endswith('layer_2'):
                layer_2 = value

    if ids and (layer_1 or layer_2):
        # Resolve texture paths
        # Textures are usually relative to the properties file or in the same dir
        # If value doesn't end with .png, append it? No, usually it's the filename without extension or with.
        # In the example: superior_dragon_layer_1 (no extension)
        
        l1_path = resolve_texture_path(root_dir, layer_1) if layer_1 else None
        l2_path = resolve_texture_path(root_dir, layer_2) if layer_2 else None
        
        for item_id in ids:
            _ARMOR_TEXTURE_CACHE[item_id] = (l1_path, l2_path)

def resolve_texture_path(root_dir: str, texture_name: str) -> Optional[str]:
    if not texture_name:
        return None
    
    # Check if it has extension
    if not texture_name.endswith('.png'):
        texture_name += '.png'
        
    # Check in current dir
    path = os.path.join(root_dir, texture_name)
    if os.path.exists(path):
        return path
        
    # Check in parent?
    # Sometimes textures are in a subfolder or parent.
    # But usually they are next to properties or in ./model/
    
    # Try searching in the root_dir recursively
    for r, d, f in os.walk(root_dir):
        if texture_name in f:
            return os.path.join(r, texture_name)
            
    return None

def get_armor_textures(item_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (layer_1_path, layer_2_path) for the given item_id.
    """
    if not _CACHE_INITIALIZED:
        initialize_armor_cache()
    
    result = _ARMOR_TEXTURE_CACHE.get(item_id)
    if result:
        LOGGER.info(f"Found armor texture for {item_id}: {result}")
        return result
        
    LOGGER.warning(f"Armor texture not found for {item_id}. Cache size: {len(_ARMOR_TEXTURE_CACHE)}")
    # Try with/without ARMOR_OF_ prefix as a fallback hack
    # Also try stripping common reforge prefixes
    REFORGES = [
        "ANCIENT", "WISE", "NECROTIC", "LOVING", "RIDICULOUS", "GIANT", "SUBMERGED", 
        "JADED", "DIMENSIONAL", "RENOWNED", "SPIKED", "HYPER", "REINFORCED", "PERFECT", 
        "HEAVY", "LIGHT", "MYTHIC", "PURE", "FIERCE", "SMART", "TITANIC", "CLEAN", 
        "CUBISM", "BUSTLING", "MOSSY", "FESTIVE", "GLACIAL", "GLOSSY", "STRENGTHENED", 
        "WAXED", "FORTIFIED", "WITHERED", "FABLED", "SUSPICIOUS", "GILDED", "WARPED", 
        "BULKY", "HASTY", "GRAND", "RAPID", "DEADLY", "FINE", "UNPLEASANT", "AWKWARD",
        "RICH", "PRECISE", "SPIRITUAL", "HEADSTRONG", "FRUITFUL", "MAGNETIC", "FLEET",
        "MITHRAIC", "AUSPICIOUS", "REFINED", "STELLAR", "GOBLIN", "HEATED", "AMBERED",
        "PRECURSORS", "BLOOD_SOAKED", "SALTY", "TREACHEROUS", "TOIL", "BLESSED", "EARTHEN",
        "PROSPEROUS", "MOIL", "DIRTY", "CHOMP", "PITCHIN"
    ]
    
    candidates = [item_id]
    if item_id.startswith("ARMOR_OF_"):
        candidates.append(item_id.replace("ARMOR_OF_", ""))
    else:
        candidates.append("ARMOR_OF_" + item_id)
        
    # Add candidates with reforges stripped
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
             LOGGER.info(f"Found armor texture for {item_id} using candidate {candidate}")
             return _ARMOR_TEXTURE_CACHE[candidate]
             
    return (None, None)

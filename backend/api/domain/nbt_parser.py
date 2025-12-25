"""
NBT 데이터 파싱 유틸리티

Hypixel API는 아이템 데이터를 base64로 인코딩된 NBT 형식으로 제공합니다.
이 모듈은 NBT 데이터를 파싱하여 필요한 정보를 추출합니다.
"""

import base64
import gzip
import io
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import nbtlib

LOGGER = logging.getLogger(__name__)

# C++ 확장 모듈 로드 시도
try:
    import altsky_cpp
    USE_CPP_PARSER = True
except ImportError:
    USE_CPP_PARSER = False
    LOGGER.warning("altsky_cpp module not found, using Python implementation")

# Minecraft 색상 코드 제거를 위한 패턴
MC_COLOR_PATTERN = re.compile(r'§[0-9a-fk-or]', re.IGNORECASE)

# 스탯 이름 매핑 (lore에서 사용되는 이름 -> 내부 스탯 이름)
# 주의: 이 맵은 C++ 확장 모듈(cpp_src/lore_parser.cpp)에도 정의되어 있습니다.
# 변경 시 두 곳 모두 업데이트해야 합니다.
STAT_NAME_MAP = {
    'health': 'health',
    'defense': 'defense',
    'strength': 'strength',
    'speed': 'speed',
    'crit chance': 'crit_chance',
    'crit damage': 'crit_damage',
    'intelligence': 'intelligence',
    'attack speed': 'bonus_attack_speed',
    'bonus attack speed': 'bonus_attack_speed',
    'ferocity': 'ferocity',
    'magic find': 'magic_find',
    'true defense': 'true_defense',
    'sea creature chance': 'sea_creature_chance',
    'trophy fish chance': 'trophy_fish_chance',
    'treasure chance': 'treasure_chance',
    'farming fortune': 'farming_fortune',
    'foraging fortune': 'foraging_fortune', 
    'mining fortune': 'mining_fortune',
    'mining speed': 'mining_speed',
    'fishing speed': 'fishing_speed',
    'pet luck': 'pet_luck',
    'ability damage': 'ability_damage',
    'vitality': 'vitality',
    'mending': 'mending',
    'health regen': 'health_regen',
    'damage': 'damage',
    'swing range': 'swing_range',
    'sweep': 'sweep',
}

def _parse_lore_stats(lore_lines: List[str]) -> Dict[str, float]:
    """
    lore 텍스트에서 스탯을 파싱합니다.
    예: "Health: +130" -> {'health': 130}
    예: "Farming Fortune: +67 (+25) (+12)" -> {'farming_fortune': 67}
    """
    if USE_CPP_PARSER:
        return altsky_cpp.parse_lore_stats(lore_lines)

    stats: Dict[str, float] = {}
    
    for line in lore_lines:
        # 색상 코드 제거
        clean_line = MC_COLOR_PATTERN.sub('', line).strip()
        
        # 빈 줄이나 특수 줄 무시
        if not clean_line or clean_line.startswith('['):
            continue
            
        # "스탯이름: +값" 또는 "스탯이름: 값" 패턴 매칭
        # 예: "Health: +130", "Defense: +40", "Farming Fortune: +67 (+25) (+12)"
        match = re.match(r'^([A-Za-z ]+):\s*([+-]?\d+(?:\.\d+)?)', clean_line)
        if match:
            stat_name = match.group(1).strip().lower()
            try:
                stat_value = float(match.group(2))
            except ValueError:
                continue
            
            # 스탯 이름 매핑
            internal_name = STAT_NAME_MAP.get(stat_name)
            if internal_name:
                stats[internal_name] = stat_value
    
    return stats


def decode_inventory_data(raw_data: Optional[str]) -> List[Dict[str, Any]]:
    """
    base64 인코딩된 인벤토리 데이터를 파싱합니다.
    
    Args:
        raw_data: base64 인코딩된 NBT 데이터
        
    Returns:
        아이템 딕셔너리 리스트
    """
    if not raw_data:
        return []
    
    try:
        decoded = base64.b64decode(raw_data)
        
        # Try to decompress gzip
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(decoded)) as f:
                unzipped = f.read()
            nbt_file = nbtlib.File.from_fileobj(io.BytesIO(unzipped))
        except OSError:
            # Not gzipped or other error, try raw
            nbt_file = nbtlib.File.from_fileobj(io.BytesIO(decoded))
            
        root = nbt_file
        items = []
        
        # Root is usually a Compound with "i" (List)
        if 'i' in root:
            for index, item_tag in enumerate(root['i']):
                parsed = _parse_item_nbt(item_tag)
                if parsed:
                    if 'slot' not in parsed:
                        parsed['slot'] = index
                    items.append(parsed)
        
        return items
    except Exception as e:
        LOGGER.warning(f"Failed to decode inventory data: {e}")
        return []


def _parse_item_nbt(item_tag: Any) -> Optional[Dict[str, Any]]:
    """개별 아이템 NBT 태그를 파싱합니다."""
    if not item_tag:
        return None
    
    item_data: Dict[str, Any] = {
        'count': 1,
        'id': None,
        'rarity': None,
        'extra_attributes': {}
    }
    
    if 'Count' in item_tag:
        item_data['count'] = int(item_tag['Count'])
    if 'Slot' in item_tag:
        item_data['slot'] = int(item_tag['Slot'])
        
    if 'id' in item_tag:
        item_data['minecraft_id'] = str(item_tag['id'])
        
    if 'tag' in item_tag:
        tag_compound = item_tag['tag']
        extra_attrs = _parse_extra_attributes(tag_compound)
        if extra_attrs:
            item_data['extra_attributes'] = extra_attrs
            # Skyblock item ID
            item_data['id'] = extra_attrs.get('id')
            # Rarity 추출
            item_data['rarity'] = _extract_rarity(tag_compound)
        
        # Lore에서 스탯 파싱
        display = tag_compound.get('display', {})
        if 'color' in display:
            try:
                item_data['leather_color'] = f"#{int(display['color']):06x}"
            except (ValueError, TypeError):
                pass

        lore_list = display.get('Lore', [])
        if lore_list:
            lore_strings = [str(line) for line in lore_list]
            lore_stats = _parse_lore_stats(lore_strings)
            if lore_stats:
                item_data['extra_attributes']['lore_stats'] = lore_stats
    
    # Skyblock item ID가 없으면 무시
    if not item_data.get('id'):
        return None
    
    # Recombobulated 처리 (Rarity 업그레이드)
    if item_data.get('extra_attributes', {}).get('recombobulated'):
        current_rarity = item_data.get('rarity')
        if current_rarity:
            item_data['rarity'] = _upgrade_rarity(current_rarity)
    
    return item_data


def _parse_extra_attributes(tag_compound: Any) -> Dict[str, Any]:
    """아이템의 ExtraAttributes를 파싱합니다."""
    result: Dict[str, Any] = {}
    
    if 'ExtraAttributes' not in tag_compound:
        return result
        
    ea = tag_compound['ExtraAttributes']
    
    if 'id' in ea: result['id'] = str(ea['id'])
    if 'modifier' in ea: result['reforge'] = str(ea['modifier'])
    if 'enchantments' in ea: result['enchants'] = _parse_enchants(ea['enchantments'])
    if 'hot_potato_count' in ea: result['hot_potato_count'] = int(ea['hot_potato_count'])
    if 'gems' in ea: result['gems'] = _parse_gems(ea['gems'])
    if 'runes' in ea: result['runes'] = _parse_runes(ea['runes'])
    if 'upgrade_level' in ea: result['stars'] = int(ea['upgrade_level'])
    elif 'dungeon_item_level' in ea: result['stars'] = int(ea['dungeon_item_level'])
    if 'rarity_upgrades' in ea: result['recombobulated'] = int(ea['rarity_upgrades']) > 0
    if 'talisman_enrichment' in ea: result['enrichment'] = str(ea['talisman_enrichment'])
    if 'attributes' in ea: result['attributes'] = _parse_enchants(ea['attributes'])
    if 'art_of_war_count' in ea: result['art_of_war_count'] = int(ea['art_of_war_count'])
    if 'ethermerge' in ea: result['ethermerge'] = int(ea['ethermerge']) > 0
    if 'abiphone_contacts' in ea: result['abiphone_contacts_count'] = len(ea['abiphone_contacts'])
    if 'enderman_kills' in ea: result['enderman_kills'] = int(ea['enderman_kills'])
    if 'zombie_kills' in ea: result['zombie_kills'] = int(ea['zombie_kills'])
    
    return result


def _parse_enchants(enchants_tag: Any) -> Dict[str, int]:
    """인챈트 데이터를 파싱합니다."""
    enchants = {}
    for k, v in enchants_tag.items():
        enchants[str(k)] = int(v)
    return enchants


def _parse_gems(gems_tag: Any) -> Dict[str, Dict[str, str]]:
    """젬 데이터를 파싱합니다."""
    gems = {}
    for k, v in gems_tag.items():
        slot_name = str(k)
        quality = str(v).upper()
        gem_type = slot_name.split('_')[0] if '_' in slot_name else slot_name
        gems[slot_name] = {'type': gem_type, 'quality': quality}
    return gems


def _parse_runes(runes_tag: Any) -> Dict[str, int]:
    """룬 데이터를 파싱합니다."""
    runes = {}
    for k, v in runes_tag.items():
        runes[str(k)] = int(v)
    return runes


def _extract_rarity(tag_compound: Any) -> Optional[str]:
    """아이템의 레어리티를 추출합니다."""
    # display.Lore에서 레어리티 추출 (색상 코드 기반)
    if 'display' in tag_compound and 'Lore' in tag_compound['display']:
        lore = tag_compound['display']['Lore']
        for line in lore:
            line_str = str(line)
            if '§f§lCOMMON' in line_str: return 'COMMON'
            if '§a§lUNCOMMON' in line_str: return 'UNCOMMON'
            if '§9§lRARE' in line_str: return 'RARE'
            if '§5§lEPIC' in line_str: return 'EPIC'
            if '§6§lLEGENDARY' in line_str: return 'LEGENDARY'
            if '§d§lMYTHIC' in line_str: return 'MYTHIC'
            if '§b§lDIVINE' in line_str: return 'DIVINE'
            if '§c§lSPECIAL' in line_str: return 'SPECIAL'
            if '§c§lVERY SPECIAL' in line_str: return 'VERY_SPECIAL'
            if '§4§lSUPREME' in line_str: return 'SUPREME'
            
    return None


def _upgrade_rarity(rarity: str) -> str:
    """Recombobulator로 인한 레어리티 업그레이드를 적용합니다."""
    rarity_order = [
        'COMMON', 'UNCOMMON', 'RARE', 'EPIC', 'LEGENDARY', 
        'MYTHIC', 'DIVINE', 'SPECIAL', 'VERY_SPECIAL', 'SUPREME'
    ]
    try:
        idx = rarity_order.index(rarity.upper())
        if idx < len(rarity_order) - 1:
            return rarity_order[idx + 1]
    except ValueError:
        pass
    
    return rarity


def extract_equipment_from_profile(member_data: Dict[str, Any]) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    프로필에서 현재 착용 중인 장비를 추출합니다.
    inv_armor가 비어있으면 wardrobe에서 equipped_slot의 장비를 사용합니다.
    """
    equipment = {
        'helmet': None,
        'chestplate': None,
        'leggings': None,
        'boots': None,
        'necklace': None,
        'cloak': None,
        'belt': None,
        'gloves': None,
    }
    
    inventory = member_data.get('inventory', {})
    
    # inv_armor에서 방어구 추출
    armor_data = inventory.get('inv_armor', {}).get('data')
    armor_found = False
    
    if armor_data:
        items = decode_inventory_data(armor_data)
        LOGGER.warning(f"[DEBUG] inv_armor items count: {len(items)}")
        if items:
            LOGGER.warning(f"[DEBUG] First item extra_attributes keys: {list(items[0].get('extra_attributes', {}).keys()) if items[0] else 'None'}")
        # 슬롯 순서: [boots, leggings, chestplate, helmet]
        if len(items) > 0 and items[0]:
            equipment['boots'] = items[0]
            armor_found = True
        if len(items) > 1 and items[1]:
            equipment['leggings'] = items[1]
            armor_found = True
        if len(items) > 2 and items[2]:
            equipment['chestplate'] = items[2]
            armor_found = True
        if len(items) > 3 and items[3]:
            equipment['helmet'] = items[3]
            armor_found = True

    # inv_armor가 비어있으면 wardrobe에서 equipped_slot의 장비 사용
    if not armor_found:
        equipped_slot = inventory.get('wardrobe_equipped_slot')
        wardrobe_data = inventory.get('wardrobe_contents', {}).get('data')
        
        if equipped_slot is not None and wardrobe_data:
            try:
                slot_index = int(equipped_slot) - 1  # 1-based to 0-based
                if slot_index >= 0:
                    wardrobe_items = decode_inventory_data(wardrobe_data)
                    if wardrobe_items:
                        # Wardrobe는 9열(slots 0-8)씩 구성됨
                        # 각 슬롯은 4개의 아이템 (helmet, chestplate, leggings, boots)
                        # 슬롯 1: helmet=0, chestplate=9, leggings=18, boots=27
                        # 슬롯 2: helmet=1, chestplate=10, leggings=19, boots=28
                        # 등등...
                        helmet_idx = slot_index
                        chestplate_idx = slot_index + 9
                        leggings_idx = slot_index + 18
                        boots_idx = slot_index + 27
                        
                        if helmet_idx < len(wardrobe_items) and wardrobe_items[helmet_idx]:
                            equipment['helmet'] = wardrobe_items[helmet_idx]
                        if chestplate_idx < len(wardrobe_items) and wardrobe_items[chestplate_idx]:
                            equipment['chestplate'] = wardrobe_items[chestplate_idx]
                        if leggings_idx < len(wardrobe_items) and wardrobe_items[leggings_idx]:
                            equipment['leggings'] = wardrobe_items[leggings_idx]
                        if boots_idx < len(wardrobe_items) and wardrobe_items[boots_idx]:
                            equipment['boots'] = wardrobe_items[boots_idx]
            except (ValueError, TypeError):
                pass

    # equipment_contents에서 장신구(Necklace, Cloak, Belt, Gloves) 추출
    equipment_data = inventory.get('equipment_contents', {}).get('data')
    if equipment_data:
        items = decode_inventory_data(equipment_data)
        # 슬롯 순서: [necklace, cloak, belt, gloves]
        if len(items) > 0 and items[0]:
            equipment['necklace'] = items[0]
        if len(items) > 1 and items[1]:
            equipment['cloak'] = items[1]
        if len(items) > 2 and items[2]:
            equipment['belt'] = items[2]
        if len(items) > 3 and items[3]:
            equipment['gloves'] = items[3]
    
    return equipment


def _format_weapon_label(item_id: Optional[str]) -> Optional[str]:
    if not item_id:
        return None
    normalized = str(item_id).strip().replace("_", " ").strip()
    if not normalized:
        return None
    return " ".join(part[:1].upper() + part[1:].lower() for part in normalized.split())


def extract_weapon_candidates_from_profile(member_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    핫바(0~8) 무기 후보를 반환합니다.
    """
    inventory = member_data.get('inventory', {})
    inv_data = inventory.get('inv_contents', {}).get('data')
    if not inv_data:
        return []

    items = decode_inventory_data(inv_data)
    if not items:
        return []

    hotbar_items = [
        item for item in items
        if isinstance(item, dict)
        and isinstance(item.get('slot'), int)
        and 0 <= item.get('slot') <= 8
        and item.get('id')
    ]
    hotbar_items.sort(key=lambda item: item.get('slot', 0))

    candidates = []
    for item in hotbar_items:
        item_id = item.get('id')
        candidates.append({
            'slot': item.get('slot'),
            'id': item_id,
            'name': _format_weapon_label(item_id) or item_id,
            'rarity': item.get('rarity'),
        })
    return candidates


def extract_weapon_from_profile(
    member_data: Dict[str, Any],
    preferred_slot: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    인벤토리 핫바에서 첫 번째 아이템을 무기로 간주합니다.
    (선택 슬롯 정보가 없어서 가장 안정적인 휴리스틱)
    """
    inventory = member_data.get('inventory', {})
    inv_data = inventory.get('inv_contents', {}).get('data')
    if not inv_data:
        return None

    items = decode_inventory_data(inv_data)
    if not items:
        return None

    hotbar_items = [
        item for item in items
        if isinstance(item, dict)
        and isinstance(item.get('slot'), int)
        and 0 <= item.get('slot') <= 8
        and item.get('id')
    ]
    if hotbar_items:
        if preferred_slot is not None:
            for item in hotbar_items:
                if item.get('slot') == preferred_slot:
                    return item
        hotbar_items.sort(key=lambda item: item.get('slot', 0))
        return hotbar_items[0]

    return items[0]


def extract_accessories_from_profile(member_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    프로필에서 악세서리 가방 데이터를 추출합니다.
    """
    accessories = []
    
    # talisman_bag 또는 bag_contents에서 악세서리 추출
    inventory = member_data.get('inventory', {})
    bag_data = inventory.get('bag_contents', {}).get('talisman_bag', {}).get('data')
    
    if not bag_data:
        # Fallback to old location or different structure
        bag_data = inventory.get('talisman_bag', {}).get('data')
        
    if bag_data:
        items = decode_inventory_data(bag_data)
        for item in items:
            if item:
                accessories.append(item)
                
    return accessories


def extract_pets_from_profile(member_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    프로필에서 펫 데이터를 추출합니다.
    """
    pets = []
    
    pets_data = member_data.get('pets_data', {})
    pets_list = pets_data.get('pets', [])
    
    if not isinstance(pets_list, list):
        return pets
    
    for pet_raw in pets_list:
        if not isinstance(pet_raw, dict):
            continue
        
        pet_type = pet_raw.get('type')
        tier = pet_raw.get('tier', 'COMMON')
        xp = int(pet_raw.get('exp', 0) or 0)
        
        pet = {
            'type': pet_type,
            'tier': tier,
            'level': 1,  # 펫은 1레벨부터 시작 (0레벨 없음)
            'xp': xp,
            'active': pet_raw.get('active', False),
            'held_item': pet_raw.get('heldItem'),
            'candy_used': int(pet_raw.get('candyUsed', 0) or 0),
            'skin': pet_raw.get('skin'),
        }
        
        # 펫 레벨 계산 (XP가 있으면 레벨 계산, pet_type 전달하여 Golden Dragon 등 처리)
        if xp > 0:
            pet['level'] = _calculate_pet_level(tier, xp, pet_type)
        
        if pet['type']:
            pets.append(pet)
    
    return pets


def extract_hotm_from_profile(member_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    프로필에서 Heart of the Mountain (HOTM) 데이터를 추출합니다.
    """
    mining = member_data.get('mining_core', {})
    
    if not isinstance(mining, dict):
        return None
    
    hotm = {
        'tier': mining.get('tier', 0),
        'perks': {},
        'powder': {
            'mithril': mining.get('powder_mithril', 0),
            'gemstone': mining.get('powder_gemstone', 0),
            'glacite': mining.get('powder_glacite', 0),
        }
    }
    
    # 퍽 데이터 추출
    nodes = mining.get('nodes', {})
    if isinstance(nodes, dict):
        for perk_name, perk_level in nodes.items():
            if isinstance(perk_level, (int, float)):
                hotm['perks'][perk_name] = int(perk_level)
    
    return hotm if hotm['tier'] > 0 else None


PET_XP_REQUIREMENTS = {
  "COMMON": [
    0, 100, 210, 330, 460, 605, 765, 940, 1130, 1340, 1570, 1820, 2095, 2395, 2725, 3085, 3485, 3925, 4415, 4955, 
    5555, 6215, 6945, 7745, 8625, 9585, 10635, 11785, 13045, 14425, 15935, 17585, 19385, 21345, 23475, 25785, 
    28285, 30985, 33905, 37065, 40485, 44185, 48185, 52535, 57285, 62485, 68185, 74485, 81485, 89285, 97985, 
    107685, 118485, 130485, 143785, 158485, 174685, 192485, 211985, 233285, 256485, 281685, 309085, 338885, 
    371285, 406485, 444685, 486085, 530885, 579285, 631485, 687685, 748085, 812885, 882285, 956485, 1035685, 
    1120385, 1211085, 1308285, 1412485, 1524185, 1643885, 1772085, 1909285, 2055985, 2212685, 2380385, 2560085, 
    2752785, 2959485, 3181185, 3418885, 3673585, 3946285, 4237985, 4549685, 4883385, 5241085, 5624785
  ],
  "UNCOMMON": [
    0, 175, 365, 575, 805, 1055, 1330, 1630, 1960, 2320, 2720, 3160, 3650, 4190, 4790, 5450, 6180, 6980, 7860, 
    8820, 9870, 11020, 12280, 13660, 15170, 16820, 18620, 20580, 22710, 25020, 27520, 30220, 33140, 36300, 39720, 
    43420, 47420, 51770, 56520, 61720, 67420, 73720, 80720, 88520, 97220, 106920, 117720, 129720, 143020, 157720, 
    173920, 191720, 211220, 232520, 255720, 280920, 308320, 338120, 370520, 405720, 443920, 485320, 530120, 578520, 
    630720, 686920, 747320, 812120, 881520, 955720, 1034920, 1119620, 1210320, 1307520, 1411720, 1523420, 1643120, 
    1771320, 1908520, 2055220, 2211920, 2379620, 2559320, 2752020, 2958720, 3180420, 3418120, 3672820, 3945520, 
    4237220, 4548920, 4882620, 5240320, 5624020, 6035720, 6477420, 6954120, 7470820, 8032520, 8644220
  ],
  "RARE": [
    0, 275, 575, 905, 1265, 1665, 2105, 2595, 3135, 3735, 4395, 5125, 5925, 6805, 7765, 8815, 9965, 11225, 12605, 
    14115, 15765, 17565, 19525, 21655, 23965, 26465, 29165, 32085, 35245, 38665, 42365, 46365, 50715, 55465, 60665, 
    66365, 72665, 79665, 87465, 96165, 105865, 116665, 128665, 141965, 156665, 172865, 190665, 210165, 231465, 
    254665, 279865, 307265, 337065, 369465, 404665, 442865, 484265, 529065, 577465, 629665, 685865, 746265, 811065, 
    880465, 954665, 1033865, 1118565, 1209265, 1306465, 1410665, 1522365, 1642065, 1770265, 1907465, 2054165, 
    2210865, 2378565, 2558265, 2750965, 2957665, 3179365, 3417065, 3671765, 3944465, 4236165, 4547865, 4881565, 
    5239265, 5622965, 6034665, 6476365, 6953065, 7469765, 8031465, 8643165, 9309865, 10036565, 10828265, 
    11689965, 12626665
  ],
  "EPIC": [
    0, 440, 930, 1470, 2070, 2730, 3460, 4260, 5140, 6100, 7150, 8300, 9560, 10940, 12450, 14100, 15900, 17860, 
    19990, 22300, 24800, 27500, 30420, 33580, 37000, 40700, 44700, 49050, 53800, 59000, 64700, 71000, 78000, 85800, 
    94500, 104200, 115000, 127000, 140300, 155000, 171200, 189000, 208500, 229800, 253000, 278200, 305600, 335400, 
    367800, 403000, 441200, 482600, 527400, 575800, 628000, 684200, 744600, 809400, 878800, 953000, 1032200, 
    1116900, 1207600, 1304800, 1409000, 1520700, 1640400, 1768600, 1905800, 2052500, 2209200, 2376900, 2556600, 
    2749300, 2956000, 3177700, 3415400, 3670100, 3942800, 4234500, 4546200, 4879900, 5237600, 5621300, 6033000, 
    6474700, 6951400, 7468100, 8029800, 8641500, 9308200, 10034900, 10826600, 11688300, 12625000, 13641700, 
    14743400, 15935100, 17221800, 18608500
  ],
  "LEGENDARY": [
    0, 660, 1390, 2190, 3070, 4030, 5080, 6230, 7490, 8870, 10380, 12030, 13830, 15790, 17920, 20230, 22730, 25430, 
    28350, 31510, 34930, 38630, 42630, 46980, 51730, 56930, 62630, 68930, 75930, 83730, 92430, 102130, 112930, 
    124930, 138230, 152930, 169130, 186930, 206430, 227730, 250930, 276130, 303530, 333330, 365730, 400930, 439130, 
    480530, 525330, 573730, 625930, 682130, 742530, 807330, 876730, 950930, 1030130, 1114830, 1205530, 1302730, 
    1406930, 1518630, 1638330, 1766530, 1903730, 2050430, 2207130, 2374830, 2554530, 2747230, 2953930, 3175630, 
    3413330, 3668030, 3940730, 4232430, 4544130, 4877830, 5235530, 5619230, 6030930, 6472630, 6949330, 7466030, 
    8027730, 8639430, 9306130, 10032830, 10824530, 11686230, 12622930, 13639630, 14741330, 15933030, 17219730, 
    18606430, 20103130, 21719830, 23466530, 25353230
  ]
}

# SkyCrypt 방식의 PET_LEVELS (레벨당 필요 경험치)
# 200레벨까지 지원 (Golden Dragon용)
PET_LEVELS = [
    100, 110, 120, 130, 145, 160, 175, 190, 210, 230, 250, 275, 300, 330, 360, 400, 440, 490, 540, 600, 660, 730, 800,
    880, 960, 1050, 1150, 1260, 1380, 1510, 1650, 1800, 1960, 2130, 2310, 2500, 2700, 2920, 3160, 3420, 3700, 4000, 4350,
    4750, 5200, 5700, 6300, 7000, 7800, 8700, 9700, 10800, 12000, 13300, 14700, 16200, 17800, 19500, 21300, 23200, 25200,
    27400, 29800, 32400, 35200, 38200, 41400, 44800, 48400, 52200, 56200, 60400, 64800, 69400, 74200, 79200, 84700, 90700,
    97200, 104200, 111700, 119700, 128200, 137200, 146700, 156700, 167700, 179700, 192700, 206700, 221700, 237700, 254700,
    272700, 291700, 311700, 333700, 357700, 383700, 411700, 441700, 476700, 516700, 561700, 611700, 666700, 726700,
    791700, 861700, 936700, 1016700, 1101700, 1191700, 1286700, 1386700, 1496700, 1616700, 1746700, 1886700, 0, 5555,
    1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700,
    1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700,
    1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700,
    1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700,
    1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700,
    1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700,
    1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700,
    1886700, 1886700, 1886700, 1886700, 1886700, 1886700, 1886700,
]

# 희귀도별 레벨 오프셋 (PET_LEVELS 배열에서 시작 인덱스)
PET_RARITY_OFFSET = {
    'COMMON': 0,
    'UNCOMMON': 6,
    'RARE': 11,
    'EPIC': 16,
    'LEGENDARY': 20,
    'MYTHIC': 20,
}

def _calculate_pet_level(rarity: str, xp: float, pet_type: str = None) -> int:
    """펫 경험치를 기반으로 레벨을 계산합니다 (SkyCrypt 방식).
    
    Args:
        rarity: 펫 등급 (COMMON, UNCOMMON, RARE, EPIC, LEGENDARY, MYTHIC)
        xp: 펫 경험치
        pet_type: 펫 타입 (GOLDEN_DRAGON 등 특수 케이스 처리용)
    
    Returns:
        펫 레벨 (1-100, Golden Dragon은 1-200)
    """
    rarity = rarity.upper()
    
    # XP가 0이면 항상 레벨 1 반환 (레벨 0 방지)
    if xp <= 0:
        return 1
    
    # 최대 레벨 결정
    max_level = 200 if pet_type == 'GOLDEN_DRAGON' else 100
    
    # 희귀도별 오프셋 적용
    rarity_offset = PET_RARITY_OFFSET.get(rarity, 0)
    
    # 해당 희귀도와 최대 레벨에 맞는 레벨 테이블 추출
    levels = PET_LEVELS[rarity_offset:rarity_offset + max_level - 1]
    
    level = 1
    xp_total = 0
    
    for i in range(len(levels)):
        xp_total += levels[i]
        if xp_total > xp:
            break
        level += 1
    
    return min(level, max_level)


def extract_dungeons_from_profile(member_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    프로필에서 Dungeons (Catacombs 및 클래스) 데이터를 추출합니다.
    """
    dungeons_data = member_data.get('dungeons', {})
    
    if not isinstance(dungeons_data, dict):
        return None
    
    result = {
        'catacombs': {
            'level': 0,
            'xp': 0,
        },
        'classes': {}
    }
    
    # Catacombs 레벨 및 경험치
    dungeon_types = dungeons_data.get('dungeon_types', {})
    if isinstance(dungeon_types, dict):
        catacombs = dungeon_types.get('catacombs', {})
        if isinstance(catacombs, dict):
            result['catacombs']['level'] = int(catacombs.get('level', 0) or 0)
            result['catacombs']['xp'] = int(catacombs.get('experience', 0) or 0)
    
    # 클래스 레벨
    player_classes = dungeons_data.get('player_classes', {})
    if isinstance(player_classes, dict):
        for class_name in ['healer', 'mage', 'berserk', 'archer', 'tank']:
            class_data = player_classes.get(class_name, {})
            if isinstance(class_data, dict):
                level = int(class_data.get('level', 0) or 0)
                xp = int(class_data.get('experience', 0) or 0)
                if level > 0 or xp > 0:
                    result['classes'][class_name] = {
                        'level': level,
                        'xp': xp,
                    }
    
    # 데이터가 있으면 반환
    has_data = result['catacombs']['level'] > 0 or result['catacombs']['xp'] > 0 or len(result['classes']) > 0
    return result if has_data else None

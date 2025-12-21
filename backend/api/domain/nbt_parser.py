"""
NBT 데이터 파싱 유틸리티

Hypixel API는 아이템 데이터를 base64로 인코딩된 NBT 형식으로 제공합니다.
이 모듈은 NBT 데이터를 파싱하여 필요한 정보를 추출합니다.
"""

import base64
import gzip
import io
import logging
from typing import Any, Dict, List, Optional

import nbtlib

LOGGER = logging.getLogger(__name__)


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
        print(f"DEBUG: Root keys: {root.keys()}")
        items = []
        
        # Root is usually a Compound with "i" (List)
        if 'i' in root:
            for item_tag in root['i']:
                parsed = _parse_item_nbt(item_tag)
                if parsed:
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
    
    # inv_armor에서 방어구 추출
    inventory = member_data.get('inventory', {})
    armor_data = inventory.get('inv_armor', {}).get('data')
    
    if armor_data:
        items = decode_inventory_data(armor_data)
        # 슬롯 순서: [boots, leggings, chestplate, helmet]
        if len(items) > 0 and items[0]:
            equipment['boots'] = items[0]
        if len(items) > 1 and items[1]:
            equipment['leggings'] = items[1]
        if len(items) > 2 and items[2]:
            equipment['chestplate'] = items[2]
        if len(items) > 3 and items[3]:
            equipment['helmet'] = items[3]

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
        
        pet = {
            'type': pet_raw.get('type'),
            'tier': pet_raw.get('tier'),
            'level': 0,
            'xp': int(pet_raw.get('exp', 0) or 0),
            'active': pet_raw.get('active', False),
            'held_item': pet_raw.get('heldItem'),
            'candy_used': int(pet_raw.get('candyUsed', 0) or 0),
            'skin': pet_raw.get('skin'),
        }
        
        # 펫 레벨 계산
        xp = pet.get('xp', 0)
        tier = pet.get('tier', 'COMMON')
        if xp > 0:
            pet['level'] = _calculate_pet_level(tier, xp)
        
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

def _calculate_pet_level(rarity: str, xp: float) -> int:
    """펫 경험치를 기반으로 레벨을 계산합니다."""
    rarity = rarity.upper()
    if rarity == 'MYTHIC':
        rarity = 'LEGENDARY'
    
    table = PET_XP_REQUIREMENTS.get(rarity)
    if not table:
        # 기본값: Common 테이블 사용
        table = PET_XP_REQUIREMENTS['COMMON']
    
    level = 1
    for i, req_xp in enumerate(table):
        if xp >= req_xp:
            level = i + 1
        else:
            break
    
    return min(100, level)


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

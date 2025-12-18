"""
NBT 데이터 파싱 유틸리티

Hypixel API는 아이템 데이터를 base64로 인코딩된 NBT 형식으로 제공합니다.
이 모듈은 NBT 데이터를 파싱하여 필요한 정보를 추출합니다.
"""

import base64
import gzip
import logging
from typing import Any, Dict, List, Optional

try:
    from nbt import nbt  # type: ignore
except ImportError:
    nbt = None

LOGGER = logging.getLogger(__name__)


def decode_inventory_data(raw_data: Optional[str]) -> List[Dict[str, Any]]:
    """
    base64 인코딩된 인벤토리 데이터를 파싱합니다.
    
    Args:
        raw_data: base64 인코딩된 NBT 데이터
        
    Returns:
        아이템 딕셔너리 리스트
    """
    if not raw_data or nbt is None:
        return []
    
    try:
        decoded = base64.b64decode(raw_data)
        nbt_data = nbt.NBTFile(fileobj=gzip.GzipFile(fileobj=__import__('io').BytesIO(decoded)))
        
        items = []
        if hasattr(nbt_data, 'tags') and nbt_data.tags:
            for item_tag in nbt_data.tags:
                if hasattr(item_tag, 'name') and item_tag.name == 'i':
                    for slot in item_tag.tags:
                        parsed = _parse_item_nbt(slot)
                        if parsed:
                            items.append(parsed)
        
        return items
    except Exception as e:
        LOGGER.warning(f"Failed to decode inventory data: {e}")
        return []


def _parse_item_nbt(item_tag: Any) -> Optional[Dict[str, Any]]:
    """개별 아이템 NBT 태그를 파싱합니다."""
    if not item_tag or not hasattr(item_tag, 'tags'):
        return None
    
    item_data: Dict[str, Any] = {
        'count': 1,
        'id': None,
        'rarity': None,
        'extra_attributes': {}
    }
    
    for tag in item_tag.tags:
        if not hasattr(tag, 'name'):
            continue
            
        tag_name = str(tag.name)
        
        if tag_name == 'Count':
            item_data['count'] = int(tag.value) if hasattr(tag, 'value') else 1
        elif tag_name == 'id':
            item_data['minecraft_id'] = str(tag.value) if hasattr(tag, 'value') else None
        elif tag_name == 'tag':
            # ExtraAttributes 추출
            extra_attrs = _parse_extra_attributes(tag)
            if extra_attrs:
                item_data['extra_attributes'] = extra_attrs
                # Skyblock item ID
                item_data['id'] = extra_attrs.get('id')
                # Rarity 추출 (일부 아이템은 display.Lore에서 추출 필요)
                item_data['rarity'] = _extract_rarity(tag)
    
    # Skyblock item ID가 없으면 무시
    if not item_data.get('id'):
        return None
    
    # Recombobulated 처리 (Rarity 업그레이드)
    if item_data.get('recombobulated'):
        current_rarity = item_data.get('rarity')
        if current_rarity:
            item_data['rarity'] = _upgrade_rarity(current_rarity)
    
    return item_data


def _upgrade_rarity(rarity: str) -> str:
    """Recombobulator로 인한 레어리티 업그레이드를 적용합니다."""
    rarity_order = [
        'COMMON', 'UNCOMMON', 'RARE', 'EPIC', 'LEGENDARY', 
        'MYTHIC', 'DIVINE', 'SPECIAL', 'VERY_SPECIAL'
    ]
    
    try:
        idx = rarity_order.index(rarity.upper())
        if idx < len(rarity_order) - 1:
            return rarity_order[idx + 1]
    except ValueError:
        pass
    
    return rarity


def _extract_rarity(tag_compound: Any) -> Optional[str]:
    """아이템의 레어리티를 추출합니다."""
    if not hasattr(tag_compound, 'tags'):
        return None
    
    for subtag in tag_compound.tags:
        if not hasattr(subtag, 'name'):
            continue
        
        if str(subtag.name) == 'ExtraAttributes':
            if hasattr(subtag, 'tags'):
                for attr in subtag.tags:
                    if hasattr(attr, 'name') and str(attr.name) == 'rarity' and hasattr(attr, 'value'):
                        return str(attr.value).upper()
        
        # display.Lore에서 레어리티 추출 (색상 코드 기반)
        if str(subtag.name) == 'display':
            if hasattr(subtag, 'tags'):
                for display_attr in subtag.tags:
                    if hasattr(display_attr, 'name') and str(display_attr.name) == 'Lore':
                        if hasattr(display_attr, 'tags'):
                            for lore_line in display_attr.tags:
                                if hasattr(lore_line, 'value'):
                                    line = str(lore_line.value)
                                    if '§f§lCOMMON' in line:
                                        return 'COMMON'
                                    elif '§a§lUNCOMMON' in line:
                                        return 'UNCOMMON'
                                    elif '§9§lRARE' in line:
                                        return 'RARE'
                                    elif '§5§lEPIC' in line:
                                        return 'EPIC'
                                    elif '§6§lLEGENDARY' in line:
                                        return 'LEGENDARY'
                                    elif '§d§lMYTHIC' in line:
                                        return 'MYTHIC'
    
    return None


def _parse_extra_attributes(tag_compound: Any) -> Dict[str, Any]:
    """아이템의 ExtraAttributes를 파싱합니다."""
    result: Dict[str, Any] = {}
    
    if not hasattr(tag_compound, 'tags'):
        return result
    
    for subtag in tag_compound.tags:
        if not hasattr(subtag, 'name'):
            continue
        
        name = str(subtag.name)
        
        if name == 'ExtraAttributes':
            if hasattr(subtag, 'tags'):
                for attr in subtag.tags:
                    if not hasattr(attr, 'name'):
                        continue
                    attr_name = str(attr.name)
                    
                    if attr_name == 'id':
                        result['id'] = str(attr.value) if hasattr(attr, 'value') else None
                    elif attr_name == 'modifier':
                        result['reforge'] = str(attr.value) if hasattr(attr, 'value') else None
                    elif attr_name == 'enchantments':
                        result['enchants'] = _parse_enchants(attr)
                    elif attr_name == 'hot_potato_count':
                        result['hot_potato_count'] = int(attr.value) if hasattr(attr, 'value') else 0
                    elif attr_name == 'gems':
                        result['gems'] = _parse_gems(attr)
                    elif attr_name == 'runes':
                        result['runes'] = _parse_runes(attr)
                    elif attr_name == 'upgrade_level':
                        result['stars'] = int(attr.value) if hasattr(attr, 'value') else 0
                    elif attr_name == 'dungeon_item_level':
                        result['stars'] = int(attr.value) if hasattr(attr, 'value') else 0
                    elif attr_name == 'rarity_upgrades':
                        result['recombobulated'] = int(attr.value) > 0 if hasattr(attr, 'value') else False
                    elif attr_name == 'talisman_enrichment':
                        result['enrichment'] = str(attr.value) if hasattr(attr, 'value') else None
    
    return result


def _parse_enchants(enchants_tag: Any) -> Dict[str, int]:
    """인챈트 데이터를 파싱합니다."""
    enchants = {}
    if not hasattr(enchants_tag, 'tags'):
        return enchants
    
    for enchant in enchants_tag.tags:
        if hasattr(enchant, 'name') and hasattr(enchant, 'value'):
            enchants[str(enchant.name)] = int(enchant.value)
    
    return enchants


def _parse_gems(gems_tag: Any) -> Dict[str, Dict[str, str]]:
    """젬 데이터를 파싱합니다 (타입과 품질 포함)."""
    gems = {}
    if not hasattr(gems_tag, 'tags'):
        return gems
    
    for gem_slot in gems_tag.tags:
        if not hasattr(gem_slot, 'name') or not hasattr(gem_slot, 'tags'):
            continue
        
        slot_name = str(gem_slot.name)
        gem_type = None
        gem_quality = None
        
        for attr in gem_slot.tags:
            if not hasattr(attr, 'name'):
                continue
            attr_name = str(attr.name)
            
            if attr_name == 'quality' and hasattr(attr, 'value'):
                gem_type = str(attr.value).upper()
            elif attr_name == 'uuid' or attr_name == 'unlocked_slots':
                # 젬 메타데이터, 품질 추론에 사용 가능
                pass
        
        # 품질 추론 (간략화 - 실제로는 아이템 레벨/강화 수준으로 판단)
        # 현재는 기본적으로 PERFECT로 설정
        if gem_type:
            gems[slot_name] = {
                'type': gem_type,
                'quality': gem_quality or 'PERFECT'
            }
    
    return gems


def _parse_runes(runes_tag: Any) -> Dict[str, int]:
    """룬 데이터를 파싱합니다."""
    runes = {}
    if not hasattr(runes_tag, 'tags'):
        return runes
    
    for rune in runes_tag.tags:
        if hasattr(rune, 'name') and hasattr(rune, 'value'):
            runes[str(rune.name)] = int(rune.value)
    
    return runes


def extract_equipment_from_profile(member_data: Dict[str, Any]) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    프로필에서 현재 착용 중인 장비를 추출합니다.
    
    Returns:
        helmet, chestplate, leggings, boots를 포함한 딕셔너리
    """
    equipment = {
        'helmet': None,
        'chestplate': None,
        'leggings': None,
        'boots': None,
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
    
    return equipment


def extract_accessories_from_profile(member_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    프로필에서 악세서리 가방 데이터를 추출합니다.
    """
    accessories = []
    
    # talisman_bag 또는 bag_contents에서 악세서리 추출
    inventory = member_data.get('inventory', {})
    bag_data = inventory.get('bag_contents', {})
    
    for bag_name, bag_info in bag_data.items():
        if 'talisman' in bag_name.lower():
            if isinstance(bag_info, dict):
                raw = bag_info.get('data')
                if raw:
                    items = decode_inventory_data(raw)
                    accessories.extend(items)
    
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
            'xp': pet_raw.get('exp', 0),
            'active': pet_raw.get('active', False),
            'held_item': pet_raw.get('heldItem'),
            'candy_used': pet_raw.get('candyUsed', 0),
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
            result['catacombs']['level'] = catacombs.get('level', 0) or 0
            result['catacombs']['xp'] = catacombs.get('experience', 0) or 0
    
    # 클래스 레벨
    player_classes = dungeons_data.get('player_classes', {})
    if isinstance(player_classes, dict):
        for class_name in ['healer', 'mage', 'berserk', 'archer', 'tank']:
            class_data = player_classes.get(class_name, {})
            if isinstance(class_data, dict):
                level = class_data.get('level', 0) or 0
                xp = class_data.get('experience', 0) or 0
                if level > 0 or xp > 0:
                    result['classes'][class_name] = {
                        'level': level,
                        'xp': xp,
                    }
    
    # 데이터가 있으면 반환
    has_data = result['catacombs']['level'] > 0 or result['catacombs']['xp'] > 0 or len(result['classes']) > 0
    return result if has_data else None

"""
Inventory data extraction for SkyBlock profiles.

Extracts player inventory, ender chest contents, and backpack data.
"""
from typing import Any, Dict, List, Optional

from .wardrobe import _parse_inventory_items


def parse_inventory(member_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract inventory data from a member's profile.
    
    Returns:
        Dictionary containing:
        - player_inventory: 36-slot player inventory (items 0-8 are hotbar)
        - ender_chest: Ender chest contents (typically 45 slots)
        - equipment: Currently equipped equipment (armor worn + cosmetic slots)
        - backpacks: List of backpack contents
        - personal_vault: Personal vault contents if available
        - potion_bag: Potion bag contents
        - fishing_bag: Fishing bag contents
        - sacks_bag: Sacks bag contents
        - accessory_bag: Talisman/accessory bag contents
        - quiver: Arrow quiver contents
    """
    inventory = member_data.get("inventory", {}) or {}
    bag_contents = inventory.get("bag_contents", {}) or {}
    
    result: Dict[str, Any] = {
        "player_inventory": [],
        "ender_chest": [],
        "equipment": [],
        "backpacks": [],
        "personal_vault": [],
        "potion_bag": [],
        "fishing_bag": [],
        "sacks_bag": [],
        "quiver": [],
    }
    
    # Player inventory (36 slots: 0-8 hotbar, 9-35 main inventory)
    inv_contents = inventory.get("inv_contents")
    if inv_contents:
        result["player_inventory"] = _parse_inventory_items(inv_contents)
    
    # Ender chest contents (multiple pages, 45 slots per page typically)
    ender_chest_contents = inventory.get("ender_chest_contents")
    if ender_chest_contents:
        result["ender_chest"] = _parse_inventory_items(ender_chest_contents)
    
    # Equipment slots (armor and cosmetics currently worn)
    equipment_contents = inventory.get("equipment_contents")
    if equipment_contents:
        result["equipment"] = _parse_inventory_items(equipment_contents)
    
    # Personal vault
    personal_vault = inventory.get("personal_vault_contents")
    if personal_vault:
        result["personal_vault"] = _parse_inventory_items(personal_vault)
    
    # Potion bag
    potion_bag = bag_contents.get("potion_bag")
    if potion_bag:
        result["potion_bag"] = _parse_inventory_items(potion_bag)
    
    # Fishing bag
    fishing_bag = bag_contents.get("fishing_bag")
    if fishing_bag:
        result["fishing_bag"] = _parse_inventory_items(fishing_bag)
    
    # Sacks bag (for sack of sacks)
    sacks_bag = bag_contents.get("sacks_bag")
    if sacks_bag:
        result["sacks_bag"] = _parse_inventory_items(sacks_bag)
    
    # Quiver
    quiver = bag_contents.get("quiver")
    if quiver:
        result["quiver"] = _parse_inventory_items(quiver)
    
    # Backpacks
    backpack_contents = inventory.get("backpack_contents") or {}
    backpack_icons = inventory.get("backpack_icons") or {}
    
    backpacks: List[Dict[str, Any]] = []
    
    # Process backpack slots (keys are slot numbers as strings)
    all_slots = set(backpack_contents.keys()) | set(backpack_icons.keys())
    
    for slot_key in sorted(all_slots, key=lambda x: int(x) if x.isdigit() else 999):
        try:
            slot_num = int(slot_key)
        except ValueError:
            continue
        
        backpack_data = backpack_contents.get(slot_key)
        icon_data = backpack_icons.get(slot_key)
        
        # Parse backpack icon (the backpack item itself)
        icon_items = _parse_inventory_items(icon_data) if icon_data else []
        icon_item = icon_items[0] if icon_items else None
        
        # Parse backpack contents
        contents = _parse_inventory_items(backpack_data) if backpack_data else []
        
        if icon_item or contents:
            backpacks.append({
                "slot": slot_num,
                "icon": icon_item,
                "contents": contents,
                "size": len(contents),
            })
    
    result["backpacks"] = backpacks
    
    return result


def get_inventory_summary(member_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a summary of inventory stats without full item data.
    Useful for quick overview without parsing all items.
    """
    inventory = member_data.get("inventory", {}) or {}
    bag_contents = inventory.get("bag_contents", {}) or {}
    
    def count_items(data: Optional[Dict[str, Any]]) -> int:
        if not data:
            return 0
        items = _parse_inventory_items(data)
        return sum(1 for item in items if item is not None)
    
    backpack_contents = inventory.get("backpack_contents") or {}
    total_backpack_items = 0
    backpack_count = len(backpack_contents)
    
    for backpack_data in backpack_contents.values():
        total_backpack_items += count_items(backpack_data)
    
    return {
        "player_inventory_count": count_items(inventory.get("inv_contents")),
        "ender_chest_count": count_items(inventory.get("ender_chest_contents")),
        "personal_vault_count": count_items(inventory.get("personal_vault_contents")),
        "backpack_count": backpack_count,
        "backpack_items_count": total_backpack_items,
        "potion_bag_count": count_items(bag_contents.get("potion_bag")),
        "fishing_bag_count": count_items(bag_contents.get("fishing_bag")),
        "quiver_count": count_items(bag_contents.get("quiver")),
    }

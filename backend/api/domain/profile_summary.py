from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .dungeons import extract_dungeons
from .skills import extract_skills
from .slayer import extract_slayer
from .wardrobe import parse_wardrobe
from .accessories import parse_accessories
from .minions import parse_minions
from .collections import extract_collections_from_profile
from .inventory import parse_inventory
from .networth import calculate_networth
from django.core.cache import cache

NW_LOGGER = logging.getLogger(__name__)


@dataclass
class SkyBlockLevel:
    level: int
    progress: float
    experience: int


# Active coop membership window. Some profiles keep historical/invited members
# indefinitely; we only consider members with data and either recent activity
# or recorded experience within this horizon.
ACTIVE_MEMBER_WINDOW_MS = 500 * 24 * 60 * 60 * 1000


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


def is_active_member(member: Dict[str, Any], *, now_ms: Optional[int] = None) -> bool:
    if not isinstance(member, dict):
        return False

    profile_data = member.get("profile") or {}

    first_join = _safe_int(profile_data.get("first_join") or member.get("first_join"))
    last_save = _safe_int(profile_data.get("last_save") or member.get("last_save"))

    inventory = member.get("inventory") or {}
    has_inventory = bool(inventory.get("inv_contents"))
    has_stats = bool(member.get("player_stats"))
    has_xp = bool((member.get("player_data") or {}).get("experience"))
    has_pets = bool((member.get("pets_data") or {}).get("pets"))

    confirmed = bool((profile_data.get("coop_invitation") or {}).get("confirmed", True))

    activity_ts = last_save or first_join
    current_ms = now_ms if now_ms is not None else int(datetime.now(timezone.utc).timestamp() * 1000)
    recent = activity_ts > 0 and (current_ms - activity_ts) <= ACTIVE_MEMBER_WINDOW_MS

    has_data = has_inventory or has_stats or has_xp or has_pets

    # Treat members as active only when we have data and recent activity within the window
    return confirmed and has_data and recent


def has_confirmed_membership(member: Dict[str, Any]) -> bool:
    if not isinstance(member, dict):
        return False

    profile_data = member.get("profile") or {}
    invitation = profile_data.get("coop_invitation")
    confirmed = True
    if isinstance(invitation, dict):
        confirmed = bool(invitation.get("confirmed", True))
    if not confirmed:
        return False

    first_join = _safe_int(profile_data.get("first_join") or member.get("first_join"))
    last_save = _safe_int(profile_data.get("last_save") or member.get("last_save"))
    return first_join > 0 or last_save > 0


def count_coop_members(members: Dict[str, Any], *, now_ms: Optional[int] = None) -> int:
    if not isinstance(members, dict) or not members:
        return 0

    current_ms = now_ms if now_ms is not None else int(datetime.now(timezone.utc).timestamp() * 1000)
    confirmed_members = [
        data for data in members.values() if has_confirmed_membership(data)
    ]
    if not confirmed_members:
        return 0

    active_members = sum(
        1 for data in confirmed_members if is_active_member(data, now_ms=current_ms)
    )
    return max(active_members, len(confirmed_members))


def compute_skyblock_level(member: Dict[str, Any]) -> SkyBlockLevel:
    leveling = member.get("leveling", {}) or {}
    experience = _safe_int(leveling.get("experience"))
    level = experience // 100
    progress = (experience % 100) / 100 if experience > 0 else 0.0
    return SkyBlockLevel(level=level, progress=progress, experience=experience)


STAT_VALUE_SOURCES = {
    "health": ("health",),
    "defense": ("defense",),
    "strength": ("strength",),
    "speed": ("speed",),
    "crit_chance": ("crit_chance",),
    "crit_damage": ("crit_damage",),
    "intelligence": ("intelligence",),
    "bonus_attack_speed": ("bonus_attack_speed", "attack_speed"),
    "ferocity": ("ferocity",),
    "magic_find": ("magic_find",),
    "pet_luck": ("pet_luck",),
    "true_defense": ("true_defense",),
    "sea_creature_chance": ("sea_creature_chance",),
    "ability_damage": ("ability_damage",),
    "mining_speed": ("mining_speed",),
    "mining_fortune": ("mining_fortune",),
    "farming_fortune": ("farming_fortune",),
    "foraging_fortune": ("foraging_fortune",),
    "pristine": ("pristine",),
    "fishing_speed": ("fishing_speed",),
    "health_regen": ("health_regen",),
    "vitality": ("vitality",),
    "mending": ("mending",),
    "mana_regen": ("mana_regen",),
    "alchemy_wisdom": ("alchemy_wisdom",),
    "carpentry_wisdom": ("carpentry_wisdom",),
    "combat_wisdom": ("combat_wisdom",),
    "enchanting_wisdom": ("enchanting_wisdom",),
    "farming_wisdom": ("farming_wisdom",),
    "fishing_wisdom": ("fishing_wisdom",),
    "foraging_wisdom": ("foraging_wisdom",),
    "mining_wisdom": ("mining_wisdom",),
    "runecrafting_wisdom": ("runecrafting_wisdom",),
    "social_wisdom": ("social_wisdom",),
    "taming_wisdom": ("taming_wisdom",),
    "rift_time": ("rift_time",),
    "rift_damage": ("rift_damage",),
    "rift_health": ("rift_health",),
    "rift_intelligence": ("rift_intelligence",),
    "rift_mana_regen": ("rift_mana_regen",),
    "rift_walk_speed": ("rift_walk_speed",),
    "double_hook_chance": ("double_hook_chance",),
    "sweep": ("sweep",),
}


def simplify_stats(member: Dict[str, Any]) -> Dict[str, Any]:
    stats = member.get("player_stats", {}) or {}
    player_data_stats = (
        (member.get("player_data") or {}).get("stats") if isinstance(member.get("player_data"), dict) else None
    ) or {}

    if not isinstance(stats, dict):
        stats = {}
    if not isinstance(player_data_stats, dict):
        player_data_stats = {}

    sources = [stats, player_data_stats]

    simplified: Dict[str, float] = {}
    for key, aliases in STAT_VALUE_SOURCES.items():
        candidates = aliases if isinstance(aliases, (tuple, list)) else (aliases,)
        value: Any = None
        for alias in candidates:
            for source in sources:
                candidate = source.get(alias)
                if candidate is not None:
                    value = candidate
                    break
            if value is not None:
                break

        if value is None:
            continue

        simplified[key] = _safe_float(value)

    return simplified


def summarize_currencies(member: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    currencies = member.get("currencies", {}) or {}
    purse = _safe_float(currencies.get("coin_purse"))
    motes = _safe_float(currencies.get("motes_purse"))

    coop_bank = 0.0
    personal_bank = 0.0
    banking_data = profile.get("banking") or {}
    if isinstance(banking_data, dict):
        coop_bank = _safe_float(banking_data.get("balance"))

    profile_data = member.get("profile") or {}
    if isinstance(profile_data, dict):
        personal_bank = _safe_float(profile_data.get("bank_account"))

    if personal_bank == 0.0:
        personal_bank_data = member.get("personal_bank")
        if isinstance(personal_bank_data, dict):
            personal_bank = _safe_float(
                personal_bank_data.get("balance") or personal_bank_data.get("coins")
            )
        else:
            personal_bank = _safe_float(personal_bank_data)

    bank_total = coop_bank + personal_bank
    total_coins = purse + bank_total
    essence_raw = currencies.get("essence") or {}
    essence = {
        k: _safe_int(v.get("current", 0) if isinstance(v, dict) else v)
        for k, v in essence_raw.items()
    }

    # Check for Forest Essence in other locations if not present
    if "FOREST" not in essence:
        # Check inside essence_raw for case variations
        if "forest" in essence_raw:
             val = essence_raw["forest"]
             essence["FOREST"] = _safe_int(val.get("current", 0) if isinstance(val, dict) else val)
        
        # Check currencies top level for various keys
        if "FOREST" not in essence:
            for key in ["forest_essence", "FOREST_ESSENCE", "essence_forest", "ESSENCE_FOREST", "forest", "FOREST"]:
                val = currencies.get(key)
                if val is not None:
                    essence["FOREST"] = _safe_int(val.get("current", 0) if isinstance(val, dict) else val)
                    break

    essence_total = sum(essence.values()) if essence else 0

    return {
        "purse": purse,
        "bank": {
            "coop": coop_bank,
            "personal": personal_bank,
            "total": bank_total,
        },
        "total_coins": total_coins,
        "motes": motes,
        "essence": essence,
        "essence_total": essence_total,
    }


def summarize_profile(
    player_uuid: str,
    profile: Dict[str, Any],
    *,
    achievements: Optional[Dict[str, Any]] = None,
    skip_networth: bool = False,
    skip_inventory: bool = False,
    skip_wardrobe: bool = False,
    skip_collections: bool = False,
    skip_minions: bool = False,
    skip_accessories: bool = False,
) -> Optional[Dict[str, Any]]:
    members = profile.get("members") or {}
    member = members.get(player_uuid)
    if not member:
        return None

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    cute_name = profile.get("cute_name")
    profile_id = profile.get("profile_id")
    game_mode = profile.get("game_mode") or profile.get("mode")
    last_save = _safe_int(member.get("last_save") or profile.get("last_save"))
    last_save_iso = (
        datetime.fromtimestamp(last_save / 1000, tz=timezone.utc).isoformat()
        if last_save
        else None
    )

    level = compute_skyblock_level(member)
    # Attach achievements to member for downstream skill extraction
    if achievements:
        member["__achievements"] = achievements
    skills = extract_skills(member)
    slayer_data = member.get("slayer") or member.get("slayer_bosses") or {}
    slayer = extract_slayer(slayer_data)
    dungeons = extract_dungeons(member)
    stats = simplify_stats(member)
    currency = summarize_currencies(member, profile)

    inventory_data = member.get("inventory", {}) or {}
    wardrobe_inventory = inventory_data.get("wardrobe_contents") or {}
    armor_inventory = inventory_data.get("inv_armor")

    equipped_slot = member.get("inventory", {}).get("wardrobe_equipped_slot")
    equipped_slot = _safe_int(equipped_slot) if equipped_slot is not None else None
    if equipped_slot is not None:
        # Hypixel uses -1 for "no wardrobe slot"; normalize to None.
        if equipped_slot < 0:
            equipped_slot = None

    if skip_wardrobe:
        # Only parse equipped armor if wardrobe is skipped
        wardrobe = parse_wardrobe({}, armor_inventory, equipped_slot=equipped_slot)
    else:
        wardrobe = parse_wardrobe(wardrobe_inventory, armor_inventory, equipped_slot=equipped_slot)

    # Extract collections data
    collections = {} if skip_collections else extract_collections_from_profile(member)

    # Extract inventory data
    inventory = {} if skip_inventory else parse_inventory(member)

    # Calculate networth
    networth = None
    if not skip_networth:
        try:
            # Try SkyHelper API first
            from ..skyhelper_client import fetch_networth
            networth_data = fetch_networth(profile_id, player_uuid)
            
            if networth_data:
                networth = {
                    "total": networth_data.get("networth", 0),
                    "unsoulbound": networth_data.get("unsoulboundNetworth", 0),
                    "purse": networth_data.get("purse", 0),
                    "bank": networth_data.get("bank", 0),
                    "categories": {}
                }
                
                types = networth_data.get("types", {})
                for key, data in types.items():
                    networth["categories"][key] = {
                        "name": key.replace("_", " ").title(),
                        "total": data.get("total", 0),
                        "item_count": len(data.get("items", []))
                    }
        except Exception as e:
            NW_LOGGER.warning("Failed to fetch networth from SkyHelper API: %s", e)

        if not networth:
            try:
                networth_result = calculate_networth(member, profile)
                networth = networth_result.to_dict()
            except Exception as e:
                NW_LOGGER.warning("Failed to calculate networth locally: %s", e)
                networth = None

    return {
        "profile": {
            "profile_id": profile_id,
            "cute_name": cute_name,
            "game_mode": game_mode,
            "member_count": count_coop_members(members, now_ms=now_ms),
            "last_save": last_save,
            "last_save_iso": last_save_iso,
        },
        "skyblock_level": {
            "level": level.level,
            "progress": level.progress,
            "experience": level.experience,
        },
        "skills": skills,
        "slayer": slayer,
        "dungeons": dungeons,
        "stats": stats,
        "currencies": currency,
        "wardrobe": {
            "equipped_slot": equipped_slot,
            **wardrobe,
        },
        "accessories": {} if skip_accessories else parse_accessories(member),
        "minions": {} if skip_minions else parse_minions(member, profile),
        "collections": collections,
        "inventory": inventory,
        "networth": networth,
    }


def get_cached_profile_summary(player_uuid: str, profile: Dict[str, Any], *, achievements: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    members = profile.get("members") or {}
    member = members.get(player_uuid)
    if not member:
        return None
        
    # Determine cache key based on last_save
    profile_id = profile.get("profile_id")
    last_save = member.get("last_save") or 0
    
    # Cache key includes profile_id, uuid, and last_save timestamp
    # This ensures that if the profile is updated (last_save changes), we re-compute.
    cache_key = f"profile_summary:{profile_id}:{player_uuid}:{last_save}"
    
    # Try to get from cache
    cached = cache.get(cache_key)
    if cached:
        return cached
        
    # Compute
    summary = summarize_profile(player_uuid, profile, achievements=achievements)
    
    # Cache it for 5 minutes (to keep networth prices relatively fresh)
    if summary:
        cache.set(cache_key, summary, timeout=300)
        
    return summary

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .dungeons import extract_dungeons
from .skills import extract_skills
from .slayer import extract_slayer
from .wardrobe import parse_wardrobe
from .accessories import parse_accessories


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


def compute_skyblock_level(member: Dict[str, Any]) -> SkyBlockLevel:
    leveling = member.get("leveling", {}) or {}
    experience = _safe_int(leveling.get("experience"))
    level = experience // 100
    progress = (experience % 100) / 100 if experience > 0 else 0.0
    return SkyBlockLevel(level=level, progress=progress, experience=experience)


def simplify_stats(member: Dict[str, Any]) -> Dict[str, Any]:
    stats = member.get("player_stats", {}) or {}

    keys = [
        "health",
        "defense",
        "strength",
        "crit_chance",
        "crit_damage",
        "attack_speed",
        "intelligence",
        "speed",
        "ferocity",
        "magic_find",
        "pet_luck",
        "true_defense",
    ]

    simplified = {}
    for key in keys:
        val = stats.get(key)
        if val is None:
            continue
        simplified[key] = _safe_float(val)
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


def summarize_profile(player_uuid: str, profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    members = profile.get("members") or {}
    member = members.get(player_uuid)
    if not member:
        return None

    def _active_members_count() -> int:
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        active = sum(1 for data in members.values() if is_active_member(data, now_ms=now_ms))
        return active

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
    skills = extract_skills(member)
    slayer = extract_slayer(member.get("slayer", {}))
    dungeons = extract_dungeons(member)
    stats = simplify_stats(member)
    currency = summarize_currencies(member, profile)

    inventory_data = member.get("inventory", {}) or {}
    wardrobe_inventory = inventory_data.get("wardrobe_contents") or {}
    armor_inventory = inventory_data.get("inv_armor")
    wardrobe = parse_wardrobe(wardrobe_inventory, armor_inventory)
    equipped_slot = member.get("inventory", {}).get("wardrobe_equipped_slot")

    return {
        "profile": {
            "profile_id": profile_id,
            "cute_name": cute_name,
            "game_mode": game_mode,
            "member_count": _active_members_count(),
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
            "equipped_slot": _safe_int(equipped_slot) if equipped_slot is not None else None,
            **wardrobe,
        },
        "accessories": parse_accessories(member),
    }

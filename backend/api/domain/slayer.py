import re
from typing import Any, Dict

# Boss-specific XP thresholds (level 0..9). These differ slightly for some bosses in early levels.
BOSS_LEVELS = {
    "zombie": [0, 5, 15, 200, 1000, 5000, 20000, 100000, 400000, 1000000],
    "spider": [0, 5, 15, 200, 1000, 5000, 20000, 100000, 400000, 1000000],
    "wolf": [0, 5, 15, 200, 1000, 5000, 20000, 100000, 400000, 1000000],
    "enderman": [0, 5, 15, 200, 1000, 5000, 20000, 100000, 400000, 1000000],
    "blaze": [0, 5, 15, 200, 1000, 5000, 20000, 100000, 400000, 1000000],
    # Vampire (Riftstalker) caps at 5 (claimed_levels preferred, this is only a fallback)
    "vampire": [0, 15, 200, 1000, 5000, 20000],
}


def xp_to_level(boss: str, xp: int) -> int:
    levels = BOSS_LEVELS.get(boss, BOSS_LEVELS["zombie"])
    lvl = 0
    for i, need in enumerate(levels):
        if xp >= need:
            lvl = i
        else:
            break
    return lvl


BOSSES = ["zombie", "spider", "wolf", "enderman", "blaze", "vampire"]


def level_from_claimed(claimed: Dict[str, Any]) -> int | None:
    """
    Hypixel stores claimed_levels like {"level_1": true, "level_2": true, ...}.
    We prefer this over XP because some slayers (e.g., Riftstalker Bloodfiend) have
    different caps and XP curves.
    """
    if not isinstance(claimed, dict):
        return None
    best = None
    for key, value in claimed.items():
        if not value:
            continue
        match = re.search(r"(\\d+)", str(key))
        if not match:
            continue
        try:
            number = int(match.group(1))
        except ValueError:
            continue
        best = number if best is None else max(best, number)
    return best


def extract_slayer(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Hypixel v2 returns a nested compound with slayer_bosses. Accept either the member root
    or the slayer sub-dictionary for compatibility.
    """
    if isinstance(data, dict):
        if "slayer_bosses" in data:
            slayer = data.get("slayer_bosses") or {}
        elif "slayer" in data and isinstance(data["slayer"], dict):
            slayer = data["slayer"].get("slayer_bosses", {}) or {}
        else:
            slayer = {}
    else:
        slayer = {}

    out: Dict[str, Any] = {}
    total_xp = 0

    for boss in BOSSES:
        boss_data = slayer.get(boss, {}) or {}
        xp_raw = boss_data.get("xp", 0) or 0
        try:
            xp = int(xp_raw)
        except (TypeError, ValueError):
            try:
                xp = int(float(xp_raw))
            except (TypeError, ValueError):
                xp = 0
        claimed_levels = boss_data.get("claimed_levels") or {}
        lvl_from_claims = level_from_claimed(claimed_levels)
        lvl = lvl_from_claims if lvl_from_claims is not None else xp_to_level(boss, xp)
        out[boss] = {"xp": xp, "level": lvl}
        total_xp += xp

    out["total_xp"] = total_xp
    return out

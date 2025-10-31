from typing import Any, Dict

# Approximate XP thresholds for Slayer levels 0-9.
SLAYER_LEVELS = [0, 5, 15, 200, 1000, 5000, 20000, 100000, 400000, 1000000]


def xp_to_level(xp: int) -> int:
    lvl = 0
    for i, need in enumerate(SLAYER_LEVELS):
        if xp >= need:
            lvl = i
        else:
            break
    return lvl


BOSSES = ["zombie", "spider", "wolf", "enderman", "blaze", "vampire"]


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
        lvl = xp_to_level(xp)
        out[boss] = {"xp": xp, "level": lvl}
        total_xp += xp

    out["total_xp"] = total_xp
    return out

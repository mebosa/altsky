from typing import Any, Dict

# Approximate XP thresholds for Catacombs levels 0-50.
CATACOMBS_LEVELS = [
    0,
    50,
    125,
    235,
    395,
    625,
    955,
    1425,
    2095,
    3045,
    4385,
    6275,
    8940,
    12700,
    17970,
    25340,
    35640,
    50040,
    70040,
    97640,
    135640,
    188140,
    259640,
    356640,
    488640,
    668640,
    911640,
    1239640,
    1684640,
    2284640,
    3084640,
    4149640,
    5569640,
    7459640,
    9989640,
    13389640,
    17889640,
    23889640,
    31889640,
    42689640,
    57189640,
    76689640,
    102189640,
    135189640,
    178189640,
    234189640,
    307189640,
    403189640,
    528189640,
    690189640,
]


def xp_to_level(xp: int) -> int:
    lvl = 0
    for i, need in enumerate(CATACOMBS_LEVELS):
        if xp >= need:
            lvl = i
        else:
            break
    return min(lvl, 50)


CLASSES = ["healer", "mage", "berserk", "archer", "tank"]


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


def extract_dungeons(member: Dict[str, Any]) -> Dict[str, Any]:
    dungeon_data = member.get("dungeons", {}) or {}

    catacombs_raw = dungeon_data.get("dungeon_types", {}).get("catacombs", {}) or {}
    catacombs_xp = _safe_int(catacombs_raw.get("experience"))
    catacombs_level = xp_to_level(catacombs_xp)

    classes_raw = dungeon_data.get("player_classes", {}) or {}
    classes_out: Dict[str, Dict[str, int]] = {}
    for cls in CLASSES:
        xp = _safe_int(classes_raw.get(cls, {}).get("experience"))
        classes_out[cls] = {"xp": xp, "level": xp_to_level(xp)}

    return {
        "catacombs": {"xp": catacombs_xp, "level": catacombs_level},
        "classes": classes_out,
    }

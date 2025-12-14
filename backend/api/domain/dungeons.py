from dataclasses import dataclass
from typing import Any, Dict

# XP thresholds for Catacombs levels 0-50 (cumulative).
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
    17960,
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
    5559640,
    7459640,
    9959640,
    13259640,
    17559640,
    23159640,
    30359640,
    39559640,
    51559640,
    66559640,
    85559640,
    109559640,
    139559640,
    177559640,
    225559640,
    285559640,
    360559640,
    453559640,
    569809640,  # Level 50 cap
]


@dataclass
class DungeonStat:
    level: int
    xp: int
    progress: float
    current: int
    to_next: int
    overflow: int


def xp_to_stat(xp: int) -> DungeonStat:
    """
    Convert raw XP into a level/progress snapshot with overflow tracking.
    """
    if xp <= 0:
        need = CATACOMBS_LEVELS[1] - CATACOMBS_LEVELS[0]
        return DungeonStat(level=0, xp=0, progress=0.0, current=0, to_next=need, overflow=0)

    cap_level = len(CATACOMBS_LEVELS) - 1
    level = 0
    for i in range(1, cap_level + 1):
        if xp >= CATACOMBS_LEVELS[i]:
            level = i
        else:
            break

    overflow = max(0, xp - CATACOMBS_LEVELS[-1])

    if level >= cap_level:
        base = CATACOMBS_LEVELS[cap_level]
        return DungeonStat(
            level=cap_level,
            xp=xp,
            progress=1.0,
            current=xp - base,
            to_next=0,
            overflow=overflow,
        )

    base = CATACOMBS_LEVELS[level]
    need = CATACOMBS_LEVELS[level + 1] - base
    have = xp - base
    progress = max(0.0, min(1.0, have / need)) if need else 1.0
    return DungeonStat(
        level=level,
        xp=xp,
        progress=progress,
        current=have,
        to_next=need,
        overflow=0,
    )


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
    catacombs = xp_to_stat(catacombs_xp)

    classes_raw = dungeon_data.get("player_classes", {}) or {}
    classes_out: Dict[str, Dict[str, int]] = {}
    for cls in CLASSES:
        xp = _safe_int(classes_raw.get(cls, {}).get("experience"))
        stat = xp_to_stat(xp)
        classes_out[cls] = {
            "xp": stat.xp,
            "level": stat.level,
            "progress": stat.progress,
            "current": stat.current,
            "to_next": stat.to_next,
            "overflow": stat.overflow,
        }

    return {
        "catacombs": {
            "xp": catacombs.xp,
            "level": catacombs.level,
            "progress": catacombs.progress,
            "current": catacombs.current,
            "to_next": catacombs.to_next,
            "overflow": catacombs.overflow,
        },
        "classes": classes_out,
    }

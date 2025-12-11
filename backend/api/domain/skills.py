from dataclasses import dataclass
from typing import Any, Dict, Tuple, List

# Default XP thresholds for most skills (levels 0-60). Last value is placeholder until official tables are published.
DEFAULT_SKILL_XP_TABLE = [
    0,
    50,
    175,
    375,
    675,
    1175,
    1925,
    2925,
    4425,
    6425,
    9925,
    14925,
    22425,
    32425,
    47425,
    67425,
    97425,
    147425,
    222425,
    322425,
    522425,
    822425,
    1222425,
    1722425,
    2322425,
    3022425,
    3822425,
    4722425,
    5722425,
    6822425,
    8022425,
    9322425,
    10722425,
    12222425,
    13822425,
    15522425,
    17322425,
    19222425,
    21222425,
    23322425,
    25522425,
    27822425,
    30222425,
    32722425,
    35322425,
    38022425,
    40822425,
    43722425,
    46722425,
    49822425,
    53022425,
    56322425,
    59722425,
    63222425,
    66822425,
    70522425,
    74322425,
    78222425,
    82222425,
    86322425,
    90522425,
]

# RuneCrafting has its own curve and caps at 25.
RUNECRAFTING_XP_TABLE = [
    0,
    50,
    150,
    250,
    500,
    1000,
    2000,
    3500,
    6000,
    10000,
    15000,
    21500,
    30000,
    40000,
    52000,
    66000,
    82000,
    100000,
    120000,
    150000,
    200000,
    275000,
    380000,
    525000,
    700000,
]

SKILL_XP_TABLES: Dict[str, List[int]] = {
    "runecrafting": RUNECRAFTING_XP_TABLE,
}

MAX_SKILL_LEVELS: Dict[str, int] = {
    "fishing": 50,
    "foraging": 54,
    "alchemy": 50,
    "carpentry": 50,
    "runecrafting": len(RUNECRAFTING_XP_TABLE) - 1,
}
DEFAULT_MAX_SKILL_LEVEL = 60

# Legacy key (v1) -> Modern key (v2) mapping
SKILL_KEY_MAP: Dict[str, Tuple[str, str]] = {
    "farming": ("experience_skill_farming", "SKILL_FARMING"),
    "mining": ("experience_skill_mining", "SKILL_MINING"),
    "combat": ("experience_skill_combat", "SKILL_COMBAT"),
    "foraging": ("experience_skill_foraging", "SKILL_FORAGING"),
    "fishing": ("experience_skill_fishing", "SKILL_FISHING"),
    "enchanting": ("experience_skill_enchanting", "SKILL_ENCHANTING"),
    "alchemy": ("experience_skill_alchemy", "SKILL_ALCHEMY"),
    "taming": ("experience_skill_taming", "SKILL_TAMING"),
    "carpentry": ("experience_skill_carpentry", "SKILL_CARPENTRY"),
    "runecrafting": ("experience_skill_runecrafting", "SKILL_RUNECRAFTING"),
    "social": ("experience_skill_social2", "SKILL_SOCIAL"),
}


@dataclass
class SkillStat:
    level: int
    progress: float  # 0~1
    xp: int
    xp_current: int
    xp_for_next: int


def xp_to_level(skill: str, xp: int) -> SkillStat:
    table = SKILL_XP_TABLES.get(skill, DEFAULT_SKILL_XP_TABLE)
    max_level = MAX_SKILL_LEVELS.get(skill, DEFAULT_MAX_SKILL_LEVEL)

    if xp <= 0:
        return SkillStat(0, 0.0, 0, 0, table[1] - table[0])

    lvl = 0
    for i in range(1, min(max_level, len(table) - 1) + 1):
        if xp >= table[i]:
            lvl = i
        else:
            break

    if lvl >= max_level:
        return SkillStat(max_level, 1.0, xp, xp - table[max_level], 0)

    base = table[lvl]
    need = table[lvl + 1] - base
    have = xp - base
    progress = max(0.0, min(1.0, have / need)) if need > 0 else 1.0
    return SkillStat(lvl, progress, xp, have, need)


def _skill_xp_from_member(member: Dict[str, Any], legacy_key: str, modern_key: str) -> int:
    """
    Hypixel profile v2 moves skill XP to player_data.experience entries.
    Fall back to the legacy top-level keys if present.
    """
    if legacy_key in member:
        value = member.get(legacy_key) or 0
    else:
        player_data = member.get("player_data") or {}
        experience = player_data.get("experience") or {}
        value = experience.get(modern_key) or 0

    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


def extract_skills(member: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    total_lvl = 0.0
    counted = 0

    for name, (legacy_key, modern_key) in SKILL_KEY_MAP.items():
        xp = _skill_xp_from_member(member, legacy_key, modern_key)
        stat = xp_to_level(name, xp)
        out[name] = {
            "level": stat.level,
            "progress": stat.progress,
            "xp": stat.xp,
            "current": stat.xp_current,
            "to_next": stat.xp_for_next,
        }

        if name not in ("runecrafting", "carpentry", "social"):
            total_lvl += stat.level + stat.progress
            counted += 1

    average_level = round(total_lvl / counted, 2) if counted else 0.0
    out["average_level"] = average_level

    return out

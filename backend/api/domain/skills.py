from dataclasses import dataclass
from typing import Any, Dict, Tuple, List, Optional

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
# Source: https://hypixel-skyblock.fandom.com/wiki/Runecrafting
RUNECRAFTING_XP_TABLE = [
    0,
    50,
    150,
    275,
    435,
    635,
    885,
    1200,
    1600,
    2100,
    2725,
    3510,
    4510,
    5760,
    7325,
    9325,
    11825,
    14950,
    18950,
    23950,
    30200,
    38050,
    47850,
    60100,
    75400,
    94400,
]

SKILL_XP_TABLES: Dict[str, List[int]] = {
    "runecrafting": RUNECRAFTING_XP_TABLE,
    # Social uses the same curve/cap as Runecrafting.
    "social": RUNECRAFTING_XP_TABLE,
}

MAX_SKILL_LEVELS: Dict[str, int] = {
    "fishing": 50,
    "foraging": 50,
    "alchemy": 50,
    "taming": 60,
    "carpentry": 50,
    "runecrafting": len(RUNECRAFTING_XP_TABLE) - 1,
    "social": len(RUNECRAFTING_XP_TABLE) - 1,
}
DEFAULT_MAX_SKILL_LEVEL = 60

# Base caps and maximum additional cap upgrades available per skill.
SKILL_LEVEL_CAP_BASES: Dict[str, int] = {
    "farming": 50,
    "taming": 50,
}
SKILL_LEVEL_CAP_MAX_EXTRA: Dict[str, int] = {
    "farming": 10,
    "taming": 10,
}

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
    overflow: int


def xp_to_level(skill: str, xp: int, *, max_level_override: Optional[int] = None) -> SkillStat:
    table = SKILL_XP_TABLES.get(skill, DEFAULT_SKILL_XP_TABLE)
    default_max = MAX_SKILL_LEVELS.get(skill, DEFAULT_MAX_SKILL_LEVEL)
    table_cap = len(table) - 1
    cap_level = default_max if max_level_override is None else max_level_override
    cap_level = max(1, min(cap_level, table_cap))

    if xp <= 0:
        return SkillStat(0, 0.0, 0, 0, table[1] - table[0], 0)

    lvl = 0
    for i in range(1, cap_level + 1):
        if xp >= table[i]:
            lvl = i
        else:
            break

    if xp >= table[cap_level]:
        last_gap = table[cap_level] - table[cap_level - 1] if cap_level > 0 else 0
        overflow = xp - table[cap_level]
        return SkillStat(cap_level, 1.0, xp, last_gap, 0, overflow)

    base = table[lvl]
    need = table[lvl + 1] - base
    have = xp - base
    progress = max(0.0, min(1.0, have / need)) if need > 0 else 1.0
    return SkillStat(lvl, progress, xp, have, need, 0)


def _normalize_skill_key(value: str) -> str:
    key = (value or "").strip().lower()
    if key.startswith("skill_"):
        key = key[6:]
    for suffix in ("_level_cap", "_level_caps", "_cap", "_caps"):
        if key.endswith(suffix):
            key = key[: -len(suffix)]
    return key


def _coerce_cap_count(value: Any) -> int:
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            return int(digits)
        return 1 if value else 0
    if isinstance(value, list):
        return len(value)
    return 0


def _extract_skill_cap_counts(member: Dict[str, Any]) -> Dict[str, int]:
    """
    Skill cap upgrades can be stored in multiple places depending on future API changes.
    Gather the best-known structure into a normalized mapping for downstream use.
    """
    caps: Dict[str, int] = {}
    candidate_sources = []
    player_data = member.get("player_data") or {}
    for key in ("skill_level_caps", "skill_caps", "level_cap_upgrades"):
        raw = player_data.get(key)
        if isinstance(raw, dict):
            candidate_sources.append(raw)
    for key in ("skill_level_caps", "skill_caps"):
        raw = member.get(key)
        if isinstance(raw, dict):
            candidate_sources.append(raw)

    for source in candidate_sources:
        for raw_key, raw_value in source.items():
            normalized = _normalize_skill_key(str(raw_key))
            if not normalized:
                continue
            count = _coerce_cap_count(raw_value)
            if count <= 0:
                continue
            current = caps.get(normalized, 0)
            caps[normalized] = max(current, count)
    return caps


def _resolve_skill_cap(skill: str, unlocked_caps: Dict[str, int]) -> int:
    normalized = skill.lower()
    theoretical_max = MAX_SKILL_LEVELS.get(normalized, DEFAULT_MAX_SKILL_LEVEL)
    base_cap = SKILL_LEVEL_CAP_BASES.get(normalized)
    if base_cap is None:
        return theoretical_max
    max_extra = SKILL_LEVEL_CAP_MAX_EXTRA.get(normalized, 0)
    unlocked = min(unlocked_caps.get(normalized, 0), max_extra)
    return min(base_cap + unlocked, theoretical_max)


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
    cap_counts = _extract_skill_cap_counts(member)

    for name, (legacy_key, modern_key) in SKILL_KEY_MAP.items():
        xp = _skill_xp_from_member(member, legacy_key, modern_key)
        cap_override = _resolve_skill_cap(name, cap_counts)
        stat = xp_to_level(name, xp, max_level_override=cap_override)
        unlocked_caps = cap_counts.get(name, 0)
        out[name] = {
            "level": stat.level,
            "progress": stat.progress,
            "xp": stat.xp,
            "current": stat.xp_current,
            "to_next": stat.xp_for_next,
            "overflow": stat.overflow,
        }
        if name in SKILL_LEVEL_CAP_BASES:
            out[name]["cap"] = cap_override
            out[name]["caps_unlocked"] = min(
                unlocked_caps, SKILL_LEVEL_CAP_MAX_EXTRA.get(name, unlocked_caps)
            )

        if name not in ("runecrafting", "carpentry", "social"):
            total_lvl += stat.level + stat.progress
            counted += 1

    average_level = round(total_lvl / counted, 2) if counted else 0.0
    out["average_level"] = average_level

    return out

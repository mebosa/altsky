from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class JacobContest:
    key: str
    crop: str
    collected: int
    position: int
    participants: int
    medal: Optional[str]
    timestamp: int  # Derived from key if possible, or just keep raw key

@dataclass
class GardenData:
    level: int
    xp: int
    copper: int
    visitors_served: int
    larva_consumed: int
    medals: Dict[str, int]
    perks: Dict[str, int]
    unique_golds: List[str]
    unique_silvers: List[str]
    unique_bronzes: List[str]
    contests: List[JacobContest]

def extract_garden(member: Dict[str, Any]) -> Dict[str, Any]:
    garden_data = member.get("garden_player_data", {}) or {}
    jacob_data = member.get("jacobs_contest", {}) or {}
    
    # Basic Garden Stats
    # Note: Level and XP might be in a different place or calculated, 
    # but for now we take what's in garden_player_data if available.
    # Often level is not directly in garden_player_data in the public API, 
    # but we can try to find it. If not, we default to 0.
    level = 0 
    xp = 0
    
    copper = garden_data.get("copper", 0)
    visitors_served = garden_data.get("visitors_served", 0)
    larva_consumed = garden_data.get("larva_consumed", 0)
    
    # Jacob's Contest Stats
    medals_inv = jacob_data.get("medals_inv", {})
    medals = {
        "gold": medals_inv.get("gold", 0),
        "silver": medals_inv.get("silver", 0),
        "bronze": medals_inv.get("bronze", 0),
    }
    
    perks = jacob_data.get("perks", {})
    
    unique_brackets = jacob_data.get("unique_brackets", {})
    unique_golds = unique_brackets.get("gold", [])
    unique_silvers = unique_brackets.get("silver", [])
    unique_bronzes = unique_brackets.get("bronze", [])
    
    # Parse Contests
    contests_raw = jacob_data.get("contests", {})
    contests: List[JacobContest] = []
    
    for key, data in contests_raw.items():
        # Key format: "101:3_27:SUGAR_CANE" (Year:Month_Day:Crop)
        parts = key.split(":")
        crop = parts[-1] if len(parts) > 0 else "UNKNOWN"
        
        # Try to parse timestamp/date from key if needed, 
        # but for now we just store the key.
        
        contest = JacobContest(
            key=key,
            crop=crop,
            collected=data.get("collected", 0),
            position=data.get("claimed_position", 0),
            participants=data.get("claimed_participants", 0),
            medal=data.get("claimed_medal"),
            timestamp=0 # Placeholder
        )
        contests.append(contest)
        
    # Sort contests by something? Maybe reverse order of keys (newer first)
    # The keys are roughly chronological (Year:Month_Day)
    # But string sorting might be tricky with single digits.
    # Let's try to parse the key for sorting.
    def parse_contest_key(k):
        try:
            parts = k.key.split(":")
            year = int(parts[0])
            date_parts = parts[1].split("_")
            month = int(date_parts[0])
            day = int(date_parts[1])
            return (year, month, day)
        except:
            return (0, 0, 0)

    contests.sort(key=parse_contest_key, reverse=True)
    
    return asdict(GardenData(
        level=level,
        xp=xp,
        copper=copper,
        visitors_served=visitors_served,
        larva_consumed=larva_consumed,
        medals=medals,
        perks=perks,
        unique_golds=unique_golds,
        unique_silvers=unique_silvers,
        unique_bronzes=unique_bronzes,
        contests=contests
    ))

import json
import requests
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from api.domain.nbt_parser import _parse_lore_stats

STATSCALC_URL = "http://localhost:8082"

def test_full_flow_with_lore():
    # 1. Test Lore Parsing
    lore = [
        "§7Damage: §c+500",
        "§7Strength: §c+325",
        "§7Crit Damage: §c+50%",
        "§7Bonus Attack Speed: §c+10%",
        "§7Intelligence: §a+250",
        "§7Ferocity: §a+30",
        "",
        "§6Ability: Giant's Slam §e§lRIGHT CLICK",
        "§7Slam your sword into the ground",
        "§7dealing §c100,000 §7damage to nearby",
        "§7enemies.",
        "§8Mana Cost: §3100",
        "§8Cooldown: §a30s",
        "",
        "§d§lMYTHIC SWORD"
    ]
    
    print("Testing Lore Parsing...")
    stats = _parse_lore_stats(lore)
    print(f"Parsed Stats: {stats}")
    
    expected_stats = {
        'damage': 500,
        'strength': 325,
        'crit_damage': 50,
        'bonus_attack_speed': 10,
        'intelligence': 250,
        'ferocity': 30
    }
    
    for k, v in expected_stats.items():
        if k not in stats:
            print(f"MISSING: {k}")
        elif stats[k] != v:
            print(f"MISMATCH: {k} expected {v}, got {stats[k]}")
            
    # 2. Test Statscalc
    print("\nTesting Statscalc...")
    payload = {
        "uuid": "test-uuid",
        "profile_id": "test-profile",
        "skills": {},
        "slayer": {},
        "equipment": {
            "weapon": {
                "id": "GIANTS_SWORD",
                "extra_attributes": {
                    "lore_stats": stats
                }
            }
        }
    }
    
    try:
        response = requests.post(f"{STATSCALC_URL}/stats", json=payload, timeout=5)
        response.raise_for_status()
        result = response.json()
        
        calc_stats = result.get('stats', {}).get('stats', {})
        print(f"Calculated Stats: {calc_stats}")
        
        if calc_stats.get('damage') == 500:
            print("SUCCESS: Damage is 500")
        else:
            print(f"FAILURE: Damage is {calc_stats.get('damage')}, expected 500")
            
    except Exception as e:
        print(f"Statscalc request failed: {e}")

if __name__ == "__main__":
    test_full_flow_with_lore()

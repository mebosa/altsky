
PET_RARITY_OFFSET = {
    "common": 0,
    "uncommon": 6,
    "rare": 11,
    "epic": 16,
    "legendary": 20,
    "mythic": 20,
}

PET_LEVELS = [
  100, 110, 120, 130, 145, 160, 175, 190, 210, 230, 250, 275, 300, 330, 360, 400, 440, 490, 540, 600, 660, 730, 800,
  880, 960, 1050, 1150, 1260, 1380, 1510, 1650, 1800, 1960, 2130, 2310, 2500, 2700, 2920, 3160, 3420, 3700, 4000, 4350,
  4750, 5200, 5700, 6300, 7000, 7800, 8700, 9700, 10800, 12000, 13300, 14700, 16200, 17800, 19500, 21300, 23200, 25200,
  27400, 29800, 32400, 35200, 38200, 41400, 44800, 48400, 52200, 56200, 60400, 64800, 69400, 74200, 79200, 84700, 90700,
  97200, 104200, 111700, 119700, 128200, 137200, 146700, 156700, 167700, 179700, 192700, 206700, 221700, 237700, 254700,
  272700, 291700, 311700, 333700, 357700, 383700, 411700, 441700, 476700, 516700, 561700, 611700, 666700, 726700,
  791700, 861700, 936700, 1016700, 1101700, 1191700, 1286700, 1386700, 1496700, 1616700, 1746700, 1886700
]

# Note: I excluded the trailing 0, 5555 and repeated 1886700 for now, assuming they are for levels > 100 or special cases.
# Let's verify the length.

print(f"Length of PET_LEVELS: {len(PET_LEVELS)}")

def get_cumulative_xp(rarity, max_level=100):
    offset = PET_RARITY_OFFSET[rarity.lower()]
    cumulative_xp = [0] # Level 1 is 0 XP
    current_xp = 0
    
    # We need to calculate up to level 100.
    # To reach level L, we need sum of PET_LEVELS[offset] to PET_LEVELS[offset + L - 2]
    # So for level 2, we need PET_LEVELS[offset]
    # For level 100, we need PET_LEVELS[offset] ... PET_LEVELS[offset + 98]
    
    for i in range(max_level - 1):
        index = offset + i
        if index >= len(PET_LEVELS):
            print(f"Warning: Index {index} out of bounds for rarity {rarity} at level {i+2}")
            break
        xp_needed = PET_LEVELS[index]
        current_xp += xp_needed
        cumulative_xp.append(current_xp)
        
    return cumulative_xp

rarities = ["common", "uncommon", "rare", "epic", "legendary"]
results = {}

for rarity in rarities:
    results[rarity] = get_cumulative_xp(rarity)

import json
print(json.dumps(results, indent=2))

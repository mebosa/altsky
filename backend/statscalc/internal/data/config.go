package data

import "sort"

// Config는 계산기에 필요한 모든 스탯 정의를 메모리에 보관합니다.
type Config struct {
	BaseStats    map[string]float64
	LevelBonuses map[string][]LevelBonus
	// 확장된 데이터 구조
	ArmorStats        map[string]map[string]float64       // item_id -> stats
	WeaponStats       map[string]map[string]float64       // item_id -> stats
	ArmorSets         map[string]ArmorSet                 // set_name -> set_bonus
	Reforges          map[string]ReforgeData              // reforge -> rarity -> stats
	Gems              map[string]GemData                  // gem_type -> quality -> stats
	Enchants          map[string]EnchantData              // enchant -> data
	Accessories       map[string]map[string]float64       // accessory_id -> stats
	Enrichments       map[string]map[string]float64       // enrichment -> stats
	Pets              map[string]map[string]PetTierData   // pet_type -> tier -> data
	PetItems          map[string]map[string]float64       // pet_item -> stats
	HOTMTiers         []HOTMTier                          // tier bonuses
	HOTMPerks         map[string]HOTMPerk                 // perk -> data
	CatacombsBonuses  []LevelBonus                        // catacombs level -> stats
	ClassBonuses      map[string][]LevelBonus             // class name -> level -> stats
	Powers            map[string]map[string]float64       // power_name -> base_stats
	PowerMultipliers  map[string]float64                  // stat -> multiplier
	Attributes        map[string]AttributeData            // attribute -> data
}

type ArmorSet struct {
	RequiredPieces     int                `json:"required_pieces"`
	SetBonus           map[string]float64 `json:"set_bonus"`
	SetBonusMultiplier map[string]float64 `json:"set_bonus_multiplier,omitempty"`
}

type ReforgeData map[string]map[string]float64 // rarity -> stats

type GemData map[string]GemQualityData // quality -> data

type GemQualityData struct {
	Stat   string             `json:"stat"`
	Values map[string]float64 `json:"values"` // rarity -> value
}

type EnchantData struct {
	PerLevel map[string]float64 `json:"per_level"`
}

type AttributeData struct {
	PerLevel map[string]float64 `json:"per_level"`
}

type PetTierData struct {
	PerLevel      map[string]float64 `json:"per_level"`
	MaxLevelBonus map[string]float64 `json:"max_level_bonus"`
}

type HOTMTier struct {
	Tier  int                `json:"tier"`
	Stats map[string]float64 `json:"stats"`
}

type HOTMPerk struct {
	MaxLevel int                    `json:"max_level"`
	PerLevel map[string]float64     `json:"per_level,omitempty"`
	Stats    map[string]float64     `json:"stats,omitempty"`
}

func newConfig() Config {
	return Config{
		BaseStats:        make(map[string]float64),
		LevelBonuses:     make(map[string][]LevelBonus),
		ArmorStats:       make(map[string]map[string]float64),
		WeaponStats:      make(map[string]map[string]float64),
		ArmorSets:        make(map[string]ArmorSet),
		Reforges:         make(map[string]ReforgeData),
		Gems:             make(map[string]GemData),
		Enchants:         make(map[string]EnchantData),
		Accessories:      make(map[string]map[string]float64),
		Enrichments:      make(map[string]map[string]float64),
		Pets:             make(map[string]map[string]PetTierData),
		PetItems:         make(map[string]map[string]float64),
		HOTMTiers:        []HOTMTier{},
		HOTMPerks:        make(map[string]HOTMPerk),
		CatacombsBonuses: []LevelBonus{},
		ClassBonuses:     make(map[string][]LevelBonus),
		Powers:           make(map[string]map[string]float64),
		PowerMultipliers: make(map[string]float64),
		Attributes:       make(map[string]AttributeData),
	}
}

// mergeBaseStats는 파일에서 읽은 베이스 스탯을 전체 설정에 합칩니다.
func (c *Config) mergeBaseStats(src map[string]float64) {
	if c.BaseStats == nil {
		c.BaseStats = make(map[string]float64)
	}
	for k, v := range src {
		c.BaseStats[k] = v
	}
}

// LevelBonus는 특정 key(skill/slayer 등)의 특정 레벨 이상 구간에 적용되는 보너스다.
type LevelBonus struct {
	Level int                `json:"level"`
	Stats map[string]float64 `json:"stats"`
}

func (c *Config) mergeLevelBonuses(src map[string][]LevelBonus) {
	if c.LevelBonuses == nil {
		c.LevelBonuses = make(map[string][]LevelBonus)
	}
	for key, bonuses := range src {
		c.LevelBonuses[key] = append(c.LevelBonuses[key], bonuses...)
		sort.Slice(c.LevelBonuses[key], func(i, j int) bool {
			return c.LevelBonuses[key][i].Level < c.LevelBonuses[key][j].Level
		})
	}
}

// Clone은 외부 노출 시 데이터 레이스를 막기 위해 깊은 복사본을 제공합니다.
func (c Config) Clone() Config {
	out := newConfig()
	for k, v := range c.BaseStats {
		out.BaseStats[k] = v
	}
	for key, bonuses := range c.LevelBonuses {
		copied := make([]LevelBonus, len(bonuses))
		for i, bonus := range bonuses {
			statsCopy := make(map[string]float64, len(bonus.Stats))
			for stat, val := range bonus.Stats {
				statsCopy[stat] = val
			}
			copied[i] = LevelBonus{
				Level: bonus.Level,
				Stats: statsCopy,
			}
		}
		out.LevelBonuses[key] = copied
	}
	return out
}

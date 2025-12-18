package data

import "sort"

// Config는 계산기에 필요한 모든 스탯 정의를 메모리에 보관합니다.
// 현재는 베이스 스탯만 포함하지만 추후 스킬/세트/슬레이어 등으로 확장될 예정입니다.
type Config struct {
	BaseStats    map[string]float64
	LevelBonuses map[string][]LevelBonus
}

func newConfig() Config {
	return Config{
		BaseStats:    make(map[string]float64),
		LevelBonuses: make(map[string][]LevelBonus),
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

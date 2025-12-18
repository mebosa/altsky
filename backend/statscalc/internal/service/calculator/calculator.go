package calculator

import (
	"fmt"
	"sync"

	"github.com/altskydev/altsky/backend/statscalc/internal/data"
	"github.com/altskydev/altsky/backend/statscalc/internal/model"
)

// Calculator는 Config와 PlayerProfile을 기반으로 스탯을 계산한다.
type Calculator struct {
	loader *data.Loader

	mu sync.RWMutex
}

func New(loader *data.Loader) *Calculator {
	return &Calculator{loader: loader}
}

// Calculate는 현재 Config를 참조해 플레이어 스탯을 계산한다.
// 지금은 베이스 스탯만 반환하며, 이후 단계에서 세부 로직을 추가한다.
func (c *Calculator) Calculate(profile model.PlayerProfile) model.StatBlock {
	config := c.loader.Current()
	out := make(model.StatBlock, len(config.BaseStats))

	for stat, baseValue := range config.BaseStats {
		out[stat] = baseValue
	}

	applySkillBonuses(out, profile, config)
	applySlayerBonuses(out, profile, config)

	return out
}

func applySkillBonuses(stats model.StatBlock, profile model.PlayerProfile, cfg data.Config) {
	for name, skill := range profile.Skills {
		if skill.Level <= 0 {
			continue
		}
		key := fmt.Sprintf("skill_%s", name)
		applyLevelBonuses(stats, key, skill.Level, cfg.LevelBonuses)
	}
}

func applySlayerBonuses(stats model.StatBlock, profile model.PlayerProfile, cfg data.Config) {
	for name, slayer := range profile.Slayer {
		if slayer.Level <= 0 {
			continue
		}
		key := fmt.Sprintf("slayer_%s", name)
		applyLevelBonuses(stats, key, slayer.Level, cfg.LevelBonuses)
	}
}

func applyLevelBonuses(stats model.StatBlock, key string, level int, bonuses map[string][]data.LevelBonus) {
	steps, ok := bonuses[key]
	if !ok || len(steps) == 0 {
		return
	}

	idx := -1
	for current := 1; current <= level; current++ {
		for idx+1 < len(steps) && steps[idx+1].Level <= current {
			idx++
		}
		if idx < 0 {
			continue
		}
		for stat, value := range steps[idx].Stats {
			stats[stat] += value
		}
	}
}

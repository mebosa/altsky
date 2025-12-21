package data

import (
	"context"
	"encoding/json"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// Loader는 data/stats 디렉터리를 주기적으로 스캔하여 JSON 파일을 읽고 Config를 구성한다.
type Loader struct {
	dir      string
	interval time.Duration

	mu       sync.RWMutex
	cfg      Config
	versions map[string]time.Time
}

type fileEnvelope struct {
	BaseStats    map[string]float64      `json:"base_stats"`
	LevelBonuses map[string][]LevelBonus `json:"level_bonuses"`
	// 확장된 필드
	ArmorStats        map[string]map[string]float64 `json:"armor_stats"`
	WeaponStats       map[string]map[string]float64 `json:"weapon_stats"`
	ArmorSets         map[string]ArmorSet           `json:"armor_sets"`
	Reforges          map[string]ReforgeData        `json:"reforges"`
	Gems              map[string]GemData            `json:"gems"`
	Enchants          map[string]EnchantData        `json:"enchants"`
	Accessories       map[string]map[string]float64 `json:"accessories"`
	Enrichments       map[string]map[string]float64 `json:"enrichments"`
	Pets              map[string]map[string]PetTierData `json:"pets"`
	PetItems          map[string]map[string]float64     `json:"pet_items"`
	HOTMTiers    struct {
		Tiers []HOTMTier `json:"tiers"`
	} `json:"hotm_tiers"`
	HOTMPerks         map[string]HOTMPerk           `json:"perks"`
	CatacombsBonuses  []LevelBonus                  `json:"catacombs_bonuses"`
	ClassBonuses      map[string][]LevelBonus       `json:"class_bonuses"`
	Powers            map[string]map[string]float64 `json:"powers"`
	PowerMultipliers  map[string]float64            `json:"multipliers"`
	PowerBaseBonuses  map[string]map[string]float64 `json:"power_base_bonuses"`
	Attributes        map[string]AttributeData      `json:"attributes"`
}

// NewLoader는 지정된 디렉터리에서 초기 데이터를 불러옵니다.
func NewLoader(dir string, interval time.Duration) (*Loader, error) {
	info, err := os.Stat(dir)
	if err != nil {
		return nil, fmt.Errorf("stats data dir: %w", err)
	}
	if !info.IsDir() {
		return nil, fmt.Errorf("stats data dir %s is not directory", dir)
	}

	l := &Loader{
		dir:      dir,
		interval: interval,
		cfg:      newConfig(),
		versions: make(map[string]time.Time),
	}

	if err := l.reload(); err != nil {
		return nil, err
	}
	return l, nil
}

// Current는 최신 Config의 복사본을 반환합니다.
func (l *Loader) Current() Config {
	l.mu.RLock()
	defer l.mu.RUnlock()
	// fmt.Printf("DEBUG: Current config Powers count: %d\n", len(l.cfg.Powers))
	return l.cfg
}

// StartWatch는 컨텍스트가 취소될 때까지 폴더를 주기적으로 확인합니다.
func (l *Loader) StartWatch(ctx context.Context) {
	ticker := time.NewTicker(l.interval)
	go func() {
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				if err := l.reloadIfChanged(); err != nil {
					fmt.Fprintf(os.Stderr, "[statscalc] reload error: %v\n", err)
				}
			}
		}
	}()
}

func (l *Loader) reloadIfChanged() error {
	changed := false
	err := filepath.WalkDir(l.dir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		if filepath.Ext(d.Name()) != ".json" {
			return nil
		}
		info, statErr := d.Info()
		if statErr != nil {
			return statErr
		}
		if last, ok := l.versions[path]; !ok || info.ModTime().After(last) {
			changed = true
		}
		return nil
	})
	if err != nil {
		return err
	}
	if !changed {
		return nil
	}
	return l.reload()
}

func (l *Loader) reload() error {
	cfg := newConfig()
	versions := make(map[string]time.Time)

	err := filepath.WalkDir(l.dir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() || filepath.Ext(d.Name()) != ".json" {
			return nil
		}
		if err := l.loadFile(path, &cfg); err != nil {
			return fmt.Errorf("load %s: %w", path, err)
		}
		info, infoErr := d.Info()
		if infoErr != nil {
			return infoErr
		}
		versions[path] = info.ModTime()
		return nil
	})
	if err != nil {
		return err
	}

	l.mu.Lock()
	l.cfg = cfg
	l.versions = versions
	l.mu.Unlock()
	return nil
}

func (l *Loader) loadFile(path string, cfg *Config) error {
	file, err := os.Open(path)
	if err != nil {
		return err
	}
	defer file.Close()

	dec := json.NewDecoder(file)
	var env fileEnvelope
	if err := dec.Decode(&env); err != nil {
		return err
	}

	// 기존 필드
	if len(env.BaseStats) > 0 {
		cfg.mergeBaseStats(env.BaseStats)
	}
	if len(env.LevelBonuses) > 0 {
		cfg.mergeLevelBonuses(env.LevelBonuses)
	}
	
	// 확장 필드
	if len(env.ArmorStats) > 0 {
		for k, v := range env.ArmorStats {
			cfg.ArmorStats[k] = v
		}
	}
	if len(env.WeaponStats) > 0 {
		for k, v := range env.WeaponStats {
			cfg.WeaponStats[k] = v
		}
	}
	if len(env.ArmorSets) > 0 {
		for k, v := range env.ArmorSets {
			cfg.ArmorSets[k] = v
		}
	}
	if len(env.Reforges) > 0 {
		for k, v := range env.Reforges {
			cfg.Reforges[k] = v
		}
	}
	if len(env.Gems) > 0 {
		for k, v := range env.Gems {
			cfg.Gems[k] = v
		}
	}
	if len(env.Enchants) > 0 {
		for k, v := range env.Enchants {
			cfg.Enchants[k] = v
		}
	}
	if len(env.Accessories) > 0 {
		for k, v := range env.Accessories {
			cfg.Accessories[k] = v
		}
	}
	if len(env.Enrichments) > 0 {
		for k, v := range env.Enrichments {
			cfg.Enrichments[k] = v
		}
	}
	if len(env.Pets) > 0 {
		for k, v := range env.Pets {
			cfg.Pets[k] = v
		}
	}
	if len(env.PetItems) > 0 {
		for k, v := range env.PetItems {
			cfg.PetItems[k] = v
		}
	}
	if len(env.HOTMTiers.Tiers) > 0 {
		cfg.HOTMTiers = append(cfg.HOTMTiers, env.HOTMTiers.Tiers...)
	}
	if len(env.HOTMPerks) > 0 {
		for k, v := range env.HOTMPerks {
			cfg.HOTMPerks[k] = v
		}
	}
	if len(env.CatacombsBonuses) > 0 {
		cfg.CatacombsBonuses = append(cfg.CatacombsBonuses, env.CatacombsBonuses...)
	}
	if len(env.ClassBonuses) > 0 {
		for k, v := range env.ClassBonuses {
			cfg.ClassBonuses[k] = v
		}
	}
	if len(env.Powers) > 0 {
		for k, v := range env.Powers {
			cfg.Powers[k] = v
		}
	}
	if len(env.PowerMultipliers) > 0 {
		for k, v := range env.PowerMultipliers {
			cfg.PowerMultipliers[k] = v
		}
	}
	if len(env.PowerBaseBonuses) > 0 {
		for k, v := range env.PowerBaseBonuses {
			cfg.PowerBaseBonuses[k] = v
		}
	}
	if len(env.Attributes) > 0 {
		for k, v := range env.Attributes {
			cfg.Attributes[k] = v
		}
	}
	
	return nil
}

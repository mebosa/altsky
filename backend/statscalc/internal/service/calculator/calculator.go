package calculator

import (
	"fmt"
	"math"
	"strings"
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
func (c *Calculator) Calculate(profile model.PlayerProfile) model.StatBlock {
	config := c.loader.Current()
	out := make(model.StatBlock, len(config.BaseStats))

	for stat, baseValue := range config.BaseStats {
		out[stat] = baseValue
	}

	applySkillBonuses(out, profile, config)
	applySlayerBonuses(out, profile, config)
	applyDungeonBonuses(out, profile, config)
	applySkyBlockLevelBonuses(out, profile)
	
	multipliers := make(map[string]float64)
	applyEquipmentBonuses(out, multipliers, profile, config)
	
	applyAccessoryBonuses(out, profile, config)
	applyPetBonuses(out, profile, config)
	applyHOTMBonuses(out, profile, config)

	// Special effects that modify base stats or multipliers
	applySpecialItemEffects(out, multipliers, profile)

	// Apply multipliers
	for stat, mult := range multipliers {
		out[stat] *= (1 + mult)
	}

	return out
}

func applySpecialItemEffects(stats model.StatBlock, multipliers map[string]float64, profile model.PlayerProfile) {
	// Terminator: Divides Crit Chance by 4
	if profile.Equipment.Weapon != nil && profile.Equipment.Weapon.ID == "TERMINATOR" {
		stats["crit_chance"] /= 4
	}

	items := []*model.Item{
		profile.Equipment.Helmet,
		profile.Equipment.Chestplate,
		profile.Equipment.Leggings,
		profile.Equipment.Boots,
	}

	fdPieces := 0
	for _, item := range items {
		if item == nil {
			continue
		}
		// Final Destination
		if strings.HasPrefix(item.ID, "FINAL_DESTINATION_") {
			fdPieces++
			if kills, ok := getIntAttribute(item, "enderman_kills"); ok {
				bonus := calculateFDBonus(kills)
				stats["defense"] += bonus
			}
		}
		// Reaper Armor
		if strings.HasPrefix(item.ID, "REAPER_") {
			if kills, ok := getIntAttribute(item, "zombie_kills"); ok {
				bonus := calculateReaperBonus(kills)
				stats["defense"] += bonus
			}
		}
	}

	// Final Destination Set Bonus (Full Set)
	// Wiki: 1.25x Intelligence (Multiplier +0.25)
	if fdPieces == 4 {
		multipliers["intelligence"] += 0.25
	}
}

func getIntAttribute(item *model.Item, key string) (int, bool) {
	if item.ExtraAttributes == nil {
		return 0, false
	}
	val, ok := item.ExtraAttributes[key]
	if !ok {
		return 0, false
	}
	// JSON unmarshalling might make numbers float64
	if f, ok := val.(float64); ok {
		return int(f), true
	}
	if i, ok := val.(int); ok {
		return i, true
	}
	return 0, false
}

func calculateFDBonus(kills int) float64 {
	// Table from Wiki
	thresholds := []struct {
		kills int
		bonus float64
	}{
		{200000, 400}, {150000, 395}, {125000, 390}, {100000, 380},
		{75000, 370}, {50000, 355}, {25000, 335}, {10000, 310},
		{5000, 270}, {3500, 240}, {2500, 210}, {1750, 180},
		{1200, 150}, {800, 120}, {500, 90}, {300, 60},
		{200, 40}, {100, 20},
	}

	for _, t := range thresholds {
		if kills >= t.kills {
			return t.bonus
		}
	}
	return 0
}

func calculateReaperBonus(kills int) float64 {
	// Table from Wiki
	thresholds := []struct {
		kills int
		bonus float64
	}{
		{500000, 315}, {200000, 310}, {100000, 300}, {50000, 280},
		{25000, 260}, {15000, 240}, {10000, 220}, {7500, 200},
		{5000, 180}, {3000, 150}, {2000, 120}, {1000, 90},
		{300, 50}, {50, 20},
	}

	for _, t := range thresholds {
		if kills >= t.kills {
			return t.bonus
		}
	}
	return 0
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

// applySkyBlockLevelBonuses applies stats based on SkyBlock Level.
// +5 Health per level
// +1 Strength every 5 levels
func applySkyBlockLevelBonuses(stats model.StatBlock, profile model.PlayerProfile) {
	if profile.SkyBlockLevel <= 0 {
		return
	}

	// Health: +5 per level
	stats["health"] += float64(profile.SkyBlockLevel) * 5.0

	// Strength: +1 every 5 levels
	strengthBonus := float64(profile.SkyBlockLevel / 5)
	stats["strength"] += strengthBonus
}

// applyDungeonBonuses는 Catacombs 및 클래스 레벨 보너스를 적용합니다.
func applyDungeonBonuses(stats model.StatBlock, profile model.PlayerProfile, cfg data.Config) {
	if profile.Dungeons == nil {
		return
	}
	
	// Catacombs 레벨 보너스
	if profile.Dungeons.Catacombs.Level > 0 {
		for _, bonus := range cfg.CatacombsBonuses {
			if bonus.Level <= profile.Dungeons.Catacombs.Level {
				for stat, value := range bonus.Stats {
					stats[stat] += value
				}
			}
		}
	}
	
	// 클래스 레벨 보너스 (가장 높은 클래스 적용)
	highestClass := ""
	highestLevel := 0
	for className, classData := range profile.Dungeons.Classes {
		if classData.Level > highestLevel {
			highestClass = className
			highestLevel = classData.Level
		}
	}
	
	if highestLevel > 0 && highestClass != "" {
		if classBonuses, ok := cfg.ClassBonuses[highestClass]; ok {
			for _, bonus := range classBonuses {
				if bonus.Level <= highestLevel {
					for stat, value := range bonus.Stats {
						stats[stat] += value
					}
				}
			}
		}
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

// applyEquipmentBonuses는 장비(방어구) 스탯을 계산합니다.
func applyEquipmentBonuses(stats model.StatBlock, multipliers map[string]float64, profile model.PlayerProfile, cfg data.Config) {
	items := []*model.Item{
		profile.Equipment.Helmet,
		profile.Equipment.Chestplate,
		profile.Equipment.Leggings,
		profile.Equipment.Boots,
		profile.Equipment.Weapon, // 무기 추가
	}
	
	armorCount := make(map[string]int)
	
	for _, item := range items {
		if item == nil {
			continue
		}
		
		// 기본 아이템 스탯
		itemStats, ok := cfg.ArmorStats[item.ID]
		if !ok {
			itemStats, ok = cfg.WeaponStats[item.ID]
		}

		if ok {
			// Dungeon Stars (Outside Dungeon: +2% per star)
			starMultiplier := 1.0
			if item.Stars > 0 {
				starMultiplier += 0.02 * float64(item.Stars)
			}

			for stat, value := range itemStats {
				stats[stat] += value * starMultiplier
			}
		}
		
		// 리포지 스탯 (레어리티 고려)
		if item.Reforge != "" {
			if reforgeData, ok := cfg.Reforges[item.Reforge]; ok {
				// 레어리티가 있으면 해당 레어리티 사용, 없으면 LEGENDARY 사용
				rarity := item.Rarity
				if rarity == "" {
					rarity = "LEGENDARY"
				}
				if reforgeStats, ok := reforgeData[rarity]; ok {
					for stat, value := range reforgeStats {
						stats[stat] += value
					}
				}
			}
		}
		
		// 젬 스탯 (품질 및 레어리티 고려)
		for _, gem := range item.Gems {
			if gemData, ok := cfg.Gems[gem.Type]; ok {
				quality := gem.Quality
				if quality == "" {
					quality = "PERFECT"
				}
				if qualityData, ok := gemData[quality]; ok {
					rarity := item.Rarity
					if rarity == "" {
						rarity = "COMMON"
					}
					if val, ok := qualityData.Values[rarity]; ok {
						stats[qualityData.Stat] += val
					}
				}
			}
		}
		
		// 인챈트 스탯
		for enchantName, enchantLevel := range item.Enchants {
			if enchantData, ok := cfg.Enchants[enchantName]; ok {
				for stat, valuePerLevel := range enchantData.PerLevel {
					stats[stat] += valuePerLevel * float64(enchantLevel)
				}
			}
		}
		
		// Hot Potato Books (Armor)
		if item.HotPotatoCount > 0 {
			hpbBonus := float64(item.HotPotatoCount) * 2.0
			stats["health"] += hpbBonus
			stats["defense"] += hpbBonus
		}

		// Attributes (Crimson Isle)
		if item.ExtraAttributes != nil {
			if attrs, ok := item.ExtraAttributes["attributes"].(map[string]any); ok {
				applyAttributeBonuses(stats, attrs, cfg)
			}
			
			// Art of War (+5 Strength)
			if aow, ok := item.ExtraAttributes["art_of_war_count"].(float64); ok && aow > 0 {
				stats["strength"] += 5 * aow
			}
			
			// Etherwarp Conduit (+180 Intelligence)
			if merged, ok := item.ExtraAttributes["ethermerge"].(bool); ok && merged {
				stats["intelligence"] += 180
			}
		}
		
		// 세트 보너스 감지
		setName := detectArmorSet(item.ID)
		if setName != "" {
			armorCount[setName]++
		}
	}
	
	// 세트 보너스 적용
	for setName, count := range armorCount {
		if setData, ok := cfg.ArmorSets[setName]; ok {
			if count >= setData.RequiredPieces {
				// Additive bonuses
				for stat, value := range setData.SetBonus {
					stats[stat] += value
				}
				// Multiplicative bonuses
				for stat, value := range setData.SetBonusMultiplier {
					multipliers[stat] += value
				}
			}
		}
	}
}

// detectArmorSet은 아이템 ID에서 세트명을 추출합니다.
func detectArmorSet(itemID string) string {
	// 아이템 ID의 마지막 부분(HELMET, CHESTPLATE 등) 제거
	parts := []string{
		"_HELMET", "_CHESTPLATE", "_LEGGINGS", "_BOOTS",
		"_CP", "_PANTS", // 일부 아이템의 다른 명명
	}
	
	for _, suffix := range parts {
		if len(itemID) > len(suffix) && itemID[len(itemID)-len(suffix):] == suffix {
			return itemID[:len(itemID)-len(suffix)]
		}
	}
	
	return ""
}

func applyAttributeBonuses(stats model.StatBlock, attributes map[string]any, cfg data.Config) {
	for name, levelVal := range attributes {
		level := 0
		switch v := levelVal.(type) {
		case float64:
			level = int(v)
		case int:
			level = v
		}

		if level <= 0 {
			continue
		}

		if attrData, ok := cfg.Attributes[name]; ok {
			for stat, valPerLevel := range attrData.PerLevel {
				stats[stat] += valPerLevel * float64(level)
			}
		}
	}
}

// applyAccessoryBonuses는 악세서리 스탯을 계산합니다.
func applyAccessoryBonuses(stats model.StatBlock, profile model.PlayerProfile, cfg data.Config) {
	totalMagicalPower := 0.0
	
	for _, acc := range profile.Accessories {
		// 기본 악세서리 스탯
		if accStats, ok := cfg.Accessories[acc.ID]; ok {
			for stat, value := range accStats {
				stats[stat] += value
			}
		}
		
		// 리포지 스탯
		if acc.Reforge != "" {
			if reforgeData, ok := cfg.Reforges[acc.Reforge]; ok {
				rarity := acc.Rarity
				if rarity == "" {
					rarity = "EPIC"
				}
				if reforgeStats, ok := reforgeData[rarity]; ok {
					for stat, value := range reforgeStats {
						stats[stat] += value
					}
				}
			}
		}
		
		// 강화(Enrichment) 스탯
		if acc.Enrichment != "" {
			if enrichStats, ok := cfg.Enrichments[acc.Enrichment]; ok {
				for stat, value := range enrichStats {
					stats[stat] += value
				}
			}
		}
		
		// Magical Power 계산
		rarity := acc.Rarity
		if rarity == "" {
			rarity = "EPIC"
		}
		mp := getMagicalPowerForRarity(rarity)

		// Abiphone (Contacts / 2)
		if strings.Contains(acc.ID, "ABIPHONE") {
			if contacts, ok := acc.ExtraAttributes["abiphone_contacts_count"].(float64); ok {
				mp += math.Floor(contacts / 2.0)
			}
		}
		
		// Hegemony Artifact (Double MP)
		if acc.ID == "HEGEMONY_ARTIFACT" {
			mp *= 2
		}

		totalMagicalPower += mp
	}
	
	// Magical Power 티어 보너스 적용 (Selected Power)
	applyPowerBonuses(stats, totalMagicalPower, profile.SelectedPower, cfg)
}

// getMagicalPowerForRarity는 레어리티별 Magical Power 값을 반환합니다.
func getMagicalPowerForRarity(rarity string) float64 {
	switch rarity {
	case "COMMON":
		return 3
	case "UNCOMMON":
		return 5
	case "RARE":
		return 8
	case "EPIC":
		return 12
	case "LEGENDARY":
		return 16
	case "MYTHIC":
		return 22
	case "SPECIAL":
		return 3
	case "VERY_SPECIAL":
		return 5
	default:
		return 0
	}
}

// applyPowerBonuses applies stats based on Magical Power and Selected Power.
func applyPowerBonuses(stats model.StatBlock, totalMP float64, selectedPower string, cfg data.Config) {
	if selectedPower == "" {
		return
	}

	// Normalize power name (lowercase)
	selectedPower = strings.ToLower(selectedPower)

	powerStats, ok := cfg.Powers[selectedPower]
	if !ok {
		return
	}

	// Calculate the multiplier from Magical Power
	// Formula: 719.28 * (ln(1 + 0.0019 * MP))^1.2
	mpMultiplier := 719.28 * math.Pow(math.Log(1.0+(0.0019*totalMP)), 1.2)

	for stat, baseValue := range powerStats {
		// Get the specific multiplier for this stat
		statMultiplier := 1.0
		if val, ok := cfg.PowerMultipliers[stat]; ok {
			statMultiplier = val
		}

		// Final Value = (BasePower / 100) * StatMultiplier * mpMultiplier
		finalValue := (baseValue / 100.0) * statMultiplier * mpMultiplier
		stats[stat] += finalValue
	}
}

// applyPetBonuses는 활성화된 펫의 스탯을 계산합니다.
func applyPetBonuses(stats model.StatBlock, profile model.PlayerProfile, cfg data.Config) {
	var activePet *model.Pet
	for i := range profile.Pets {
		if profile.Pets[i].Active {
			activePet = &profile.Pets[i]
			break
		}
	}
	
	if activePet == nil {
		return
	}
	
	petData, ok := cfg.Pets[activePet.Type]
	if !ok {
		return
	}
	
	tierData, ok := petData[activePet.Tier]
	if !ok {
		return
	}
	
	// 레벨당 스탯
	for stat, valuePerLevel := range tierData.PerLevel {
		stats[stat] += valuePerLevel * float64(activePet.Level)
	}
	
	// 최대 레벨 보너스 (레벨 100 가정)
	if activePet.Level >= 100 {
		for stat, value := range tierData.MaxLevelBonus {
			stats[stat] += value
		}
	}
	
	// 펫 아이템 스탯
	if activePet.HeldItem != "" {
		if petItemStats, ok := cfg.PetItems[activePet.HeldItem]; ok {
			for stat, value := range petItemStats {
				stats[stat] += value
			}
		}
	}
}

// applyHOTMBonuses는 Heart of the Mountain 스탯을 계산합니다.
func applyHOTMBonuses(stats model.StatBlock, profile model.PlayerProfile, cfg data.Config) {
	if profile.HOTM == nil {
		return
	}
	
	// 티어 보너스
	for _, tierData := range cfg.HOTMTiers {
		if tierData.Tier <= profile.HOTM.Tier {
			for stat, value := range tierData.Stats {
				stats[stat] += value
			}
		}
	}
	
	// 퍽 보너스
	for perkName, perkLevel := range profile.HOTM.Perks {
		perkData, ok := cfg.HOTMPerks[perkName]
		if !ok || perkLevel <= 0 {
			continue
		}
		
		// per_level 타입 퍽
		if len(perkData.PerLevel) > 0 {
			for stat, valuePerLevel := range perkData.PerLevel {
				stats[stat] += valuePerLevel * float64(perkLevel)
			}
		}
		
		// 고정 스탯 퍽 (레벨 1만 되면 적용)
		if len(perkData.Stats) > 0 {
			for stat, value := range perkData.Stats {
				stats[stat] += value
			}
		}
	}
}

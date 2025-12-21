package model

// PlayerProfile은 Hypixel SkyBlock API에서 추출한 핵심 정보를 표준화한 구조체입니다.
type PlayerProfile struct {
	UUID           string            `json:"uuid"`
	ProfileID      string            `json:"profile_id"`
	SkyBlockLevel  int               `json:"skyblock_level"`
	Skills         map[string]Skill  `json:"skills"`
	Slayer         map[string]Slayer `json:"slayer"`
	Dungeons       *Dungeons         `json:"dungeons,omitempty"`
	Equipment      Equipment         `json:"equipment,omitempty"`
	Accessories    []Accessory       `json:"accessories,omitempty"`
	SelectedPower  string            `json:"selected_power,omitempty"` // 추가: 선택된 파워 (예: "itchy")
	MagicalPower   float64           `json:"magical_power,omitempty"`  // 추가: 외부에서 계산된 Magical Power
	Pets           []Pet             `json:"pets,omitempty"`
	HOTM           *HOTM             `json:"hotm,omitempty"`
	CustomMetadata map[string]any    `json:"meta,omitempty"`
}

type Skill struct {
	Level int `json:"level"`
	XP    int `json:"xp"`
}

type Slayer struct {
	Level int `json:"level"`
	XP    int `json:"xp"`
}

// Dungeons는 던전 관련 정보
type Dungeons struct {
	Catacombs DungeonType `json:"catacombs,omitempty"`
	Classes   map[string]DungeonType `json:"classes,omitempty"`
}

type DungeonType struct {
	Level int `json:"level"`
	XP    int `json:"xp,omitempty"`
}

// Equipment는 현재 착용 중인 장비(방어구 4개 + 장비 슬롯)
type Equipment struct {
	Helmet     *Item `json:"helmet,omitempty"`
	Chestplate *Item `json:"chestplate,omitempty"`
	Leggings   *Item `json:"leggings,omitempty"`
	Boots      *Item `json:"boots,omitempty"`
	// 장비 슬롯 (낚시대, 곡괭이 등)
	Weapon    *Item `json:"weapon,omitempty"`
	Equipment *Item `json:"equipment_item,omitempty"`
}

// Item은 개별 아이템 정보
type Item struct {
	ID           string            `json:"id"`                      // skyblock item ID
	Count        int               `json:"count,omitempty"`         // 개수
	Rarity       string            `json:"rarity,omitempty"`        // COMMON, UNCOMMON, RARE, EPIC, LEGENDARY, MYTHIC
	Reforge      string            `json:"reforge,omitempty"`       // 리포지
	Enchants     map[string]int    `json:"enchants,omitempty"`      // 인챈트 레벨
	HotPotatoCount int             `json:"hot_potato_count,omitempty"`
	Gems         map[string]Gem    `json:"gems,omitempty"`          // gem slot -> gem data
	Runes        map[string]int    `json:"runes,omitempty"`         // rune type -> level
	Stars        int               `json:"stars,omitempty"`         // 던전 스타
	Recombobulated bool            `json:"recombobulated,omitempty"`
	ExtraAttributes map[string]any `json:"extra_attributes,omitempty"` // 기타 NBT 데이터
}

// Gem은 젬 정보 (타입과 품질)
type Gem struct {
	Type    string `json:"type"`    // RUBY, AMETHYST, JASPER, etc.
	Quality string `json:"quality"` // ROUGH, FLAWED, FINE, FLAWLESS, PERFECT
}

// Accessory는 악세서리 정보
type Accessory struct {
	Item
	Enrichment string `json:"enrichment,omitempty"` // 강화
	Tuning     int    `json:"tuning,omitempty"`     // 튜닝 레벨 (magical power)
}

// Pet은 펫 정보
type Pet struct {
	Type       string `json:"type"`                  // PET_TYPE (예: ENDERMAN)
	Tier       string `json:"tier"`                  // COMMON, UNCOMMON, RARE, EPIC, LEGENDARY, MYTHIC
	Level      int    `json:"level"`                 // 펫 레벨
	XP         int64  `json:"xp,omitempty"`
	HeldItem   string `json:"held_item,omitempty"`   // 펫 아이템
	CandyUsed  int    `json:"candy_used,omitempty"`
	Active     bool   `json:"active,omitempty"`      // 현재 활성화된 펫
	Skin       string `json:"skin,omitempty"`
}

// HOTM은 Heart of the Mountain (광산 스킬트리)
type HOTM struct {
	Tier       int            `json:"tier"`                 // HOTM 티어 (레벨)
	Perks      map[string]int `json:"perks,omitempty"`      // perk name -> level
	Powder     *Powder        `json:"powder,omitempty"`     // 가루 정보
}

type Powder struct {
	Mithril    int64 `json:"mithril,omitempty"`
	Gemstone   int64 `json:"gemstone,omitempty"`
	Glacite    int64 `json:"glacite,omitempty"`
}

// StatBlock은 계산 결과.
type StatBlock map[string]float64

// Bonus는 스탯 보너스 출처와 값
type Bonus struct {
	Source string  `json:"source"`
	Value  float64 `json:"value"`
}

// StatDetail은 단일 스탯의 상세 내역
type StatDetail struct {
	Total   float64 `json:"total"`
	Base    float64 `json:"base"`
	Bonuses []Bonus `json:"bonuses"`
}

// StatBreakdown은 모든 스탯의 상세 내역
type StatBreakdown map[string]*StatDetail

// CalculationResult는 최종 계산 결과 (스탯 + 내역)
type CalculationResult struct {
	Stats     StatBlock     `json:"stats"`
	Breakdown StatBreakdown `json:"breakdown"`
}


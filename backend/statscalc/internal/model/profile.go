package model

// PlayerProfile은 Hypixel SkyBlock API에서 추출한 핵심 정보를 표준화한 구조체입니다.
// 추후 인벤토리/악세서리/펫 데이터가 추가될 예정입니다.
type PlayerProfile struct {
	UUID           string            `json:"uuid"`
	ProfileID      string            `json:"profile_id"`
	SkyBlockLevel  int               `json:"skyblock_level"`
	Skills         map[string]Skill  `json:"skills"`
	Slayer         map[string]Slayer `json:"slayer"`
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

// StatBlock은 계산 결과.
type StatBlock map[string]float64

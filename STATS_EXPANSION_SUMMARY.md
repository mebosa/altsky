# 스카이블럭 스탯 계산기 확장 완료 요약

## 완료된 작업

### 1. Go statscalc 데이터 모델 확장 ✅
- `backend/statscalc/internal/model/profile.go`에 Equipment, Accessories, Pets, HOTM 구조체 추가
- Item, Accessory, Pet, HOTM 타입 정의
- 리포지, 인챈트, 젬, 룬, 펫 아이템 등 상세 필드 추가

### 2. statscalc 데이터 정의 파일 생성 ✅
다음 JSON 파일들을 `backend/statscalc/data/stats/`에 생성:
- **armor.json**: 방어구 아이템별 스탯, 세트 보너스, 리포지, 젬, 인챈트
- **accessories.json**: 악세서리 스탯, 강화(enrichment), Magical Power 티어
- **pets.json**: 펫 타입별/티어별 레벨당 스탯, 펫 아이템
- **hotm.json**: HOTM 티어별 보너스, 퍽별 스탯

### 3. statscalc 계산 로직 구현 ✅
`backend/statscalc/internal/service/calculator/calculator.go`에 추가:
- `applyEquipmentBonuses`: 방어구 스탯, 리포지, 젬, 인챈트, 세트 보너스 계산
- `applyAccessoryBonuses`: 악세서리 스탯, 리포지, 강화 계산
- `applyPetBonuses`: 활성 펫의 레벨별 스탯, 펫 아이템 계산
- `applyHOTMBonuses`: HOTM 티어 및 퍽 보너스 계산

`backend/statscalc/internal/data/config.go` 및 `loader.go`도 확장하여 새 데이터 구조 로드

### 4. Django NBT 파싱 유틸리티 ✅
`backend/api/domain/nbt_parser.py` 생성:
- `decode_inventory_data`: base64 NBT 데이터 파싱
- `extract_equipment_from_profile`: 방어구 4개 슬롯 추출
- `extract_accessories_from_profile`: 악세서리 가방 데이터 추출
- `extract_pets_from_profile`: 펫 데이터 추출 및 레벨 계산
- `extract_hotm_from_profile`: HOTM 티어, 퍽, 가루 데이터 추출

### 5. Django payload 확장 ✅
`backend/api/views.py` 수정:
- `_build_statscalc_payload`: 원본 member_data를 받아 NBT 파싱 수행
- Equipment, Accessories, Pets, HOTM 데이터를 statscalc로 전송
- `_serialize_item`, `_serialize_accessory` 헬퍼 함수 추가

### 6. 프론트엔드 UI 개선 ✅
`frontend/src/routes/u/[name]/p/[profileId]/StatsTab.svelte` 수정:
- 원본 스탯과 계산된 스탯을 나란히 표시
- 차이값(difference) 계산 및 시각화
- positive(녹색)/negative(빨강) 차이 강조
- "Server-calculated" 배지 표시

## 주요 기능

### 계산 파이프라인
1. **Base Stats**: 플레이어 기본 스탯
2. **Skills & Slayer**: 스킬/슬레이어 레벨 보너스
3. **Equipment**: 방어구 + 리포지 + 인챈트 + 젬 + 세트 보너스
4. **Accessories**: 악세서리 + 리포지 + 강화 (Magical Power는 TODO)
5. **Pets**: 활성 펫의 레벨별 스탯 + 펫 아이템
6. **HOTM**: 티어 보너스 + 퍽 레벨별 스탯

### 데이터 흐름
```
Hypixel API
  ↓
Django (NBT 파싱)
  ↓
statscalc payload (JSON)
  ↓
Go statscalc (계산)
  ↓
computed_stats (JSON)
  ↓
Frontend (비교 표시)
```

## 남은 작업 (향후 개선)

### 높은 우선순위
1. **NBT 라이브러리 설치**: `pip install nbtlib` (nbt_parser.py에서 사용)
2. **세트 감지 로직 개선**: 현재는 단순 접두사 매칭, 실제로는 정확한 세트 매핑 테이블 필요
3. **Magical Power 계산**: 악세서리 레어리티별 파워 합산 및 티어 보너스
4. **펫 레벨 계산**: 정확한 펫 레벨 테이블 구현 (현재는 임시 공식)
5. **데이터 정의 확장**: 더 많은 아이템/세트/펫/HOTM 퍽 추가

### 중간 우선순위
6. **Wardrobe 지원**: 워드로브의 다른 방어구 세트 파싱
7. **인벤토리 아이템**: 손에 든 무기, 장비 슬롯 아이템
8. **Dungeon Stars**: 던전 스타 업그레이드 스탯 계산
9. **Reforge Rarity**: 리포지가 레어리티에 따라 달라지는 경우
10. **Attribute 시스템**: 장비 속성(Attribute) 스탯

### 낮은 우선순위
11. **프론트 타입 에러 수정**: 기존 iconPack, Wardrobe 관련 타입 에러
12. **에러 핸들링**: NBT 파싱 실패 시 로깅 및 fallback
13. **캐싱**: statscalc 호출 결과 캐싱
14. **단위 테스트**: 각 계산 로직에 대한 테스트 작성

## 테스트 방법

### Go statscalc 서버 실행
```powershell
cd backend/statscalc
go run ./cmd/statscalc -data ./data
```

### Django 서버 실행
```powershell
cd backend
python manage.py runserver
```

### 프론트엔드 실행
```powershell
cd frontend
npm run dev
```

### API 테스트
```powershell
# Health check
curl http://localhost:8082/health

# Stats calculation (POST)
curl -X POST http://localhost:8082/stats -H "Content-Type: application/json" -d '{...}'

# Profile summary (Django)
curl http://localhost:8000/api/u/{uuid}/p/{profile_id}
```

## 주의사항

1. **NBT 라이브러리**: Python NBT 라이브러리가 설치되지 않으면 장비/악세서리 파싱이 동작하지 않음
2. **데이터 완성도**: 현재 JSON 파일에는 샘플 데이터만 있으며, 실제 게임의 모든 아이템을 추가해야 함
3. **성능**: NBT 파싱은 비용이 높을 수 있으므로 캐싱 고려 필요
4. **Go 빌드**: statscalc는 Docker 환경에서도 실행 가능하도록 설정 필요

## 파일 변경 요약

### 생성된 파일
- `backend/statscalc/data/stats/armor.json`
- `backend/statscalc/data/stats/accessories.json`
- `backend/statscalc/data/stats/pets.json`
- `backend/statscalc/data/stats/hotm.json`
- `backend/api/domain/nbt_parser.py`

### 수정된 파일
- `backend/statscalc/internal/model/profile.go`
- `backend/statscalc/internal/data/config.go`
- `backend/statscalc/internal/data/loader.go`
- `backend/statscalc/internal/service/calculator/calculator.go`
- `backend/api/views.py`
- `frontend/src/routes/u/[name]/p/[profileId]/StatsTab.svelte`

## 다음 단계 권장 순서

1. Python NBT 라이브러리 설치 및 테스트
2. 실제 플레이어 프로필로 엔드투엔드 테스트
3. 로그 확인 및 버그 수정
4. 더 많은 아이템/세트 데이터 추가
5. Magical Power 계산 구현
6. 프론트엔드 타입 에러 수정

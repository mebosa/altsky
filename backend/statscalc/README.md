# AltSky Stat Calculator (Go)

이 디렉터리는 하이픽셀 SkyBlock 스탯을 서버 측에서 계산하기 위한 Go 기반 서비스입니다.  
현재는 기본 구조와 API 뼈대만 준비한 상태이며, 실제 계산 로직은 단계적으로 추가할 예정입니다.

## 구조

```
backend/statscalc
├── cmd/statscalc        # HTTP 서버 엔트리 포인트
├── data/stats           # JSON 기반 스탯 정의 (핫 리로드 대상)
└── internal
    ├── data             # 설정 로더 및 워처
    ├── model            # 플레이어/스탯 도메인 구조체
    └── service
        └── calculator   # 스탯 계산 파이프라인
```

## 동작 방식

1. Hypixel API 응답을 `PlayerProfile` 구조체 형식으로 POST `/stats` 엔드포인트에 전달합니다.
2. 서버는 `data/stats` 폴더의 JSON 파일을 읽어 스탯 정의를 메모리에 보관합니다.
3. 파일이 변경되면 자동으로 재로딩(핫 리로드)되어 재시작 없이 새로운 정의가 적용됩니다.
4. `Calculator`는 현재 로딩된 정의와 입력 프로필을 바탕으로 스탯을 계산해 JSON으로 반환합니다.

## 실행

```bash
cd backend/statscalc
go run ./cmd/statscalc -data ./data -addr :8082
```

옵션:

| 플래그 | 기본값 | 설명 |
| --- | --- | --- |
| `-data` | `./data` | JSON 스탯 정의 디렉터리 |
| `-addr` | `:8082` | HTTP 서버 리스닝 주소 |
| `-poll` | `2s` | 데이터 폴더 변경 감지 주기 |

## TODO

- Hypixel 인벤토리 NBT 파싱 및 아이템/세트 스탯 합산
- 스킬/슬레이어/HOTM/악세서리 파워 등 세부 계산 로직 구현
- Python(Django) API와의 연동 엔드포인트 추가
- 테스트 케이스/벤치마크

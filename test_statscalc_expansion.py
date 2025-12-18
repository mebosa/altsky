"""
statscalc 확장 기능 테스트 스크립트

Go statscalc 서버가 실행 중이어야 합니다:
cd backend/statscalc && go run ./cmd/statscalc -data ./data
"""

import json
import requests

# Go statscalc 서버 URL
STATSCALC_URL = "http://localhost:8082"

# 테스트용 페이로드 (확장된 구조)
test_payload = {
    "uuid": "test-uuid",
    "profile_id": "test-profile",
    "skills": {
        "farming": {"level": 50, "xp": 1000000},
        "mining": {"level": 45, "xp": 800000},
        "combat": {"level": 40, "xp": 600000},
    },
    "slayer": {
        "zombie": {"level": 7, "xp": 100000},
        "spider": {"level": 6, "xp": 80000},
    },
    "equipment": {
        "helmet": {
            "id": "STRONG_DRAGON_HELMET",
            "reforge": "ancient",
            "enchants": {"protection": 5, "growth": 7},
            "gems": {"RUBY_0": "RUBY"},
        },
        "chestplate": {
            "id": "STRONG_DRAGON_CHESTPLATE",
            "reforge": "ancient",
        },
        "leggings": {
            "id": "STRONG_DRAGON_LEGGINGS",
            "reforge": "ancient",
        },
        "boots": {
            "id": "STRONG_DRAGON_BOOTS",
            "reforge": "ancient",
        },
    },
    "accessories": [
        {
            "id": "HEGEMONY_ARTIFACT",
            "reforge": "shaded",
            "enrichment": "strength",
        },
        {
            "id": "SCARF_THESIS",
            "reforge": "shaded",
        },
    ],
    "pets": [
        {
            "type": "ENDERMAN",
            "tier": "LEGENDARY",
            "level": 100,
            "xp": 25353230,
            "active": True,
            "held_item": "MINOS_RELIC",
        }
    ],
    "hotm": {
        "tier": 7,
        "perks": {
            "mining_speed": 50,
            "mining_fortune": 50,
            "powder_buff": 50,
            "mining_madness": 1,
            "fortunate": 1,
        },
        "powder": {
            "mithril": 1000000,
            "gemstone": 500000,
        },
    },
}


def test_health():
    """statscalc 서버 health check"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{STATSCALC_URL}/health", timeout=3)
        response.raise_for_status()
        print(f"✓ Health check passed: {response.text}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_stats_calculation():
    """statscalc 스탯 계산 테스트"""
    print("\nTesting stats calculation endpoint...")
    try:
        response = requests.post(
            f"{STATSCALC_URL}/stats",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        response.raise_for_status()
        result = response.json()
        
        print("✓ Stats calculation successful!")
        print("\nCalculated stats:")
        stats = result.get("stats", {})
        
        # 주요 스탯 출력
        important_stats = [
            "health", "defense", "strength", "crit_damage", "crit_chance",
            "intelligence", "speed", "mining_speed", "mining_fortune"
        ]
        
        for stat in important_stats:
            if stat in stats:
                print(f"  {stat}: {stats[stat]}")
        
        print(f"\nTotal stats calculated: {len(stats)}")
        
        # 전체 응답 저장
        with open("test_statscalc_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print("\nFull result saved to: test_statscalc_result.json")
        
        return True
    except Exception as e:
        print(f"✗ Stats calculation failed: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")
        return False


def test_minimal_payload():
    """최소 페이로드 테스트 (스킬만)"""
    print("\nTesting minimal payload (skills only)...")
    minimal = {
        "uuid": "minimal-test",
        "profile_id": "minimal-profile",
        "skills": {
            "farming": {"level": 10},
        },
        "slayer": {},
    }
    
    try:
        response = requests.post(
            f"{STATSCALC_URL}/stats",
            json=minimal,
            timeout=5,
        )
        response.raise_for_status()
        result = response.json()
        print("✓ Minimal payload test passed!")
        print(f"Stats: {result.get('stats', {})}")
        return True
    except Exception as e:
        print(f"✗ Minimal payload test failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("statscalc 확장 기능 테스트")
    print("=" * 60)
    
    # Health check
    if not test_health():
        print("\n⚠ statscalc 서버가 실행 중이 아닙니다!")
        print("다음 명령어로 서버를 시작하세요:")
        print("cd backend/statscalc && go run ./cmd/statscalc -data ./data")
        exit(1)
    
    # 최소 페이로드 테스트
    test_minimal_payload()
    
    # 전체 페이로드 테스트
    test_stats_calculation()
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

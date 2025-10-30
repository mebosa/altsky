from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
import requests, os

@api_view(['GET'])
def health(_):
    return Response({'ok': True})

@api_view(['GET'])
def player_lookup(_, name: str):
    key = f'uuid:{name.lower()}'
    uuid = cache.get(key)
    if not uuid:
        r = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{name}', timeout=5)
        if r.status_code == 204 or r.status_code == 404:
            return Response({'error': 'player_not_found'}, status=404)
        r.raise_for_status()
        uuid = r.json().get('id')
        cache.set(key, uuid, 3600)
    return Response({'name': name, 'uuid': uuid})

@api_view(['GET'])
def hypixel_profile(_, uuid: str):
    """
    SkyBlock profile(s) from Hypixel for the given Minecraft UUID.
    """
    key = os.getenv('HYPIXEL_API_KEY')
    if not key:
        return Response({'error': 'HYPIXEL_API_KEY missing'}, status=500)

    try:
        r = requests.get(
            'https://api.hypixel.net/v2/skyblock/profiles',
            params={'uuid': uuid},
            headers={'API-Key': key},
            timeout=12
        )
    except requests.RequestException as e:
        return Response({'error': 'hypixel_request_failed', 'detail': str(e)}, status=502)

    # 과도한 요청
    if r.status_code == 429:
        return Response({'error': 'rate_limited'}, status=429)

    # v2는 보통 200을 주고 success 플래그/데이터로 상태를 알려줌
    if r.status_code == 200:
        body = r.json()
        # success가 False면 응답 본문 통째로 전달(키 오류 등)
        if body.get('success') is False:
            return Response({'error': 'hypixel_error', 'detail': body}, status=502)
        profiles = body.get('profiles')
        if not profiles:
            # 스카이블럭을 한 번도 안 한 계정
            return Response({'error': 'no_profiles'}, status=404)
        return Response(body)

    # 그 외 상태코드(400/404 등)도 메시지 노출
    return Response({'error': 'hypixel_http_error', 'status': r.status_code, 'text': r.text}, status=502)

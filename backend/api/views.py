from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
import requests

@api_view(['GET'])
def health(_):
    return Response({'ok': True})

@api_view(['GET'])
def player_lookup(_, name: str):
    key = f'uuid:{name.lower()}'
    uuid = cache.get(key)
    if not uuid:
        r = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{name}', timeout=5)
        if r.status_code == 204:
            return Response({'error':'not found'}, status=404)
        uuid = r.json().get('id')
        cache.set(key, uuid, 3600)
    return Response({'name': name, 'uuid': uuid})

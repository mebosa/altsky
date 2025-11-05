import logging
import mimetypes
import os
from typing import Any, Dict, Optional, Tuple

import requests
from django.core.cache import cache
from django.http import HttpResponse
from django.views.static import serve
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .decorators import rate_limit
from .domain.item_textures import load_furfsky_texture
from .domain.profile_summary import summarize_profile

LOGGER = logging.getLogger(__name__)


def serve_with_logging(request, path, document_root=None, show_indexes=False):
    LOGGER.info(f"Serving static file: {path} from {document_root}")
    return serve(request, path, document_root=document_root, show_indexes=show_indexes)


def serve_furfsky_texture(request, path):
    payload = load_furfsky_texture(path)
    if payload is None:
        LOGGER.debug("FurSky texture not found: %s", path)
        return HttpResponse(status=404)

    content_type, _ = mimetypes.guess_type(path)
    return HttpResponse(payload, content_type=content_type or "application/octet-stream")
HYPIXEL_PROFILES_URL = 'https://api.hypixel.net/v2/skyblock/profiles'


def _fetch_hypixel_profiles(uuid: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    api_key = os.getenv('HYPIXEL_API_KEY')
    if not api_key:
        return None, {'error': 'hypixel_api_key_missing', 'status': 503, 'fatal': False}

    try:
        response = requests.get(
            HYPIXEL_PROFILES_URL,
            params={'uuid': uuid},
            headers={'API-Key': api_key},
            timeout=12,
        )
    except requests.RequestException as exc:
        return None, {'error': 'hypixel_request_failed', 'detail': str(exc), 'status': 502, 'fatal': True}

    if response.status_code == 429:
        return None, {'error': 'rate_limited', 'status': 429, 'fatal': False}

    if response.status_code != 200:
        return None, {
            'error': 'hypixel_http_error',
            'status': response.status_code,
            'detail': response.text,
            'fatal': True,
        }

    body = response.json()
    if body.get('success') is False:
        return None, {'error': 'hypixel_error', 'detail': body, 'status': 502, 'fatal': True}

    profiles = body.get('profiles') or []
    if not profiles:
        return None, {'error': 'no_profiles', 'status': 404, 'fatal': False}

    return body, None


@api_view(['GET'])
def health(_: Request) -> Response:
    return Response({'ok': True})


@api_view(['GET'])
def player_lookup(_: Request, name: str) -> Response:
    if not name or len(name) > 16:  # Minecraft username max length is 16
        return Response({'error': 'invalid_username', 'message': 'Invalid username length'}, status=400)
    
    if not name.replace('_', '').isalnum():  # Only alphanumeric and underscore allowed
        return Response({'error': 'invalid_username', 'message': 'Username contains invalid characters'}, status=400)
    
    # Case-insensitive search
    name = name.lower()
    cache_key = f'uuid:{name}'
    try:
        uuid = cache.get(cache_key)
        
        if not uuid:
            try:
                result = requests.get(
                    f'https://api.mojang.com/users/profiles/minecraft/{name}',
                    timeout=5,
                )
                
                if result.status_code in (204, 404):
                    return Response(
                        {'error': 'player_not_found', 'message': f'Player {name} not found'}, 
                        status=404
                    )
                
                result.raise_for_status()
                data = result.json()
                
                if not data or 'id' not in data:
                    return Response(
                        {'error': 'invalid_response', 'message': 'Invalid response from Mojang API'},
                        status=502
                    )
                
                uuid = data['id']
                cache.set(cache_key, uuid, 3600)
                
            except requests.Timeout:
                return Response(
                    {'error': 'timeout', 'message': 'Mojang API request timed out'},
                    status=504
                )
            except requests.RequestException as e:
                return Response(
                    {'error': 'request_failed', 'message': str(e)},
                    status=502
                )
            except (ValueError, KeyError) as e:
                return Response(
                    {'error': 'parse_error', 'message': f'Failed to parse Mojang API response: {str(e)}'},
                    status=502
                )
        
        # Fetch Hypixel profiles after successful UUID lookup
        body, error = _fetch_hypixel_profiles(uuid)
        if error:
            detail = error.get('detail')
            payload = {
                'name': name,
                'uuid': uuid,
                'profiles': None,
                'error': error.get('error'),
                'message': detail if isinstance(detail, str) else error.get('error'),
            }
            if detail is not None:
                payload['error_detail'] = detail
            if 'status' in error:
                payload['error_status'] = error['status']

            if error.get('fatal'):
                return Response(payload, status=error.get('status') or 502)

            return Response(payload)

        raw_profiles = body.get('profiles') or []
        profiles = []
        for raw in raw_profiles:
            members = raw.get('members') or {}
            profiles.append({
                'profile_id': raw.get('profile_id') or raw.get('uuid'),
                'cute_name': raw.get('cute_name'),
                'name': raw.get('name'),
                'game_mode': raw.get('game_mode'),
                'last_save': raw.get('last_save'),
                'last_save_iso': raw.get('last_save_iso') or raw.get('lastSaveIso'),
                'member_count': len(members),
            })

        return Response({
            'name': name,
            'uuid': uuid,
            'profiles': profiles,
            'last_updated': body.get('last_updated') or body.get('lastUpdated')
        })
        
    except Exception as e:
        return Response({
            'error': 'server_error',
            'message': f'An unexpected error occurred: {str(e)}'
        }, status=500)


@api_view(['GET'])
def hypixel_profile(_: Request, uuid: str) -> Response:
    """
    Raw SkyBlock profile list from Hypixel for the given Minecraft UUID.
    """
    body, error = _fetch_hypixel_profiles(uuid)
    if error:
        payload = {'error': error.get('error')}
        if 'detail' in error:
            payload['detail'] = error['detail']
        return Response(payload, status=error.get('status') or 502)
    return Response(body)


@api_view(['GET'])
def hypixel_profile_summary(_: Request, uuid: str, profile_id: str) -> Response:
    """
    Enriched summary for a specific profile belonging to the given UUID.
    """
    body, error = _fetch_hypixel_profiles(uuid)
    if error:
        payload = {'error': error.get('error')}
        if 'detail' in error:
            payload['detail'] = error['detail']
        return Response(payload, status=error.get('status') or 502)

    profiles = body.get('profiles') or []
    target = None
    for candidate in profiles:
        if candidate.get('profile_id') == profile_id or candidate.get('uuid') == profile_id:
            target = candidate
            break

    if not target:
        return Response({'error': 'profile_not_found'}, status=404)

    summary = summarize_profile(uuid, target)
    if not summary:
        return Response({'error': 'member_not_in_profile'}, status=404)

    return Response(
        {
            'ok': True,
            'last_updated': body.get('last_updated') or body.get('lastUpdated'),
            **summary,
        }
    )

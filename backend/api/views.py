import base64
import json
import logging
import mimetypes
import os
from datetime import datetime, timezone
from functools import lru_cache
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont
from django.core.cache import cache
from django.http import HttpResponse
from django.views.static import serve
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .decorators import rate_limit
from .domain.item_textures import load_furfsky_texture, TEXTURE_PACKS, resolve_item_icon_variants, resolve_item_icon_for_pack
from .domain.profile_summary import count_coop_members, summarize_profile, get_cached_profile_summary
from .domain.armor_textures import get_armor_textures
from .domain.museum import parse_museum, get_museum_summary, get_missing_items, get_cached_museum_summary
from .domain.collections import extract_collections_from_profile
from .domain.wardrobe import (
    _decode_bytes,
    _tag_value,
    _component_to_plain,
    _component_to_colored,
    _extract_extra_texture,
    _extract_skull_icon,
    _detect_rarity,
    _extract_leather_color,
    _parse_inventory_items,
)
from . import statscalc_client
from .http_client import session as _SESSION
from .domain.bazaar_allocator.calibrator import Calibrator, default_global_params
from .domain.bazaar_allocator.data import load_caps_from_dict, to_market_snapshot
from .domain.bazaar_allocator.optimizer import allocate
from .domain.bazaar_allocator.types import AllocatorConfig

LOGGER = logging.getLogger(__name__)



def _read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return default


def _is_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


def _should_bypass_cache(query_params: Optional[Any]) -> bool:
    if not query_params:
        return False
    raw = query_params.get('refresh')
    if raw is None:
        raw = query_params.get('force')
    return _is_truthy(raw)


def serve_with_logging(request, path, document_root=None, show_indexes=False):
    LOGGER.info(f"Serving static file: {path} from {document_root}")
    return serve(request, path, document_root=document_root, show_indexes=show_indexes)


def serve_furfsky_texture(request, path):
    payload = load_furfsky_texture(path)
    if payload is None:
        LOGGER.debug("FurSky texture not found: %s", path)
        return HttpResponse(status=404)

    content_type, _ = mimetypes.guess_type(path)
    response = HttpResponse(payload, content_type=content_type or "application/octet-stream")
    response["Access-Control-Allow-Origin"] = "*"
    return response


VANILLA_TEXTURE_CACHE_DIR = os.path.join(os.path.dirname(__file__), "domain", "texture_cache")
VANILLA_ASSET_BASE = (
    "https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.20.1"
    "/assets/minecraft/textures"
)


@lru_cache(maxsize=256)
def _get_vanilla_texture_content(path: str) -> Optional[bytes]:
    # Ensure cache directory exists
    os.makedirs(VANILLA_TEXTURE_CACHE_DIR, exist_ok=True)
    
    # Generate cache filename
    safe_filename = path.replace("/", "_").replace("\\", "_")
    cache_path = os.path.join(VANILLA_TEXTURE_CACHE_DIR, f"vanilla_{safe_filename}")
    
    # Check if cached on disk
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                return f.read()
        except OSError:
            pass
    
    # Fetch from GitHub
    url = f"{VANILLA_ASSET_BASE}/{path}"
    try:
        response = _SESSION.get(url, timeout=10)
        if response.status_code != 200:
            LOGGER.debug("Vanilla texture not found: %s (status=%s)", path, response.status_code)
            return None
        
        payload = response.content
        
        # Cache the response to disk
        try:
            with open(cache_path, "wb") as f:
                f.write(payload)
        except OSError as exc:
            LOGGER.warning("Failed to cache vanilla texture %s: %s", path, exc)
        
        return payload
        
    except requests.RequestException as exc:
        LOGGER.warning("Failed to fetch vanilla texture %s: %s", path, exc)
        return None


def serve_vanilla_texture(request, path):
    """
    Proxy vanilla Minecraft textures from GitHub, caching locally to avoid CORS issues.
    """
    payload = _get_vanilla_texture_content(path)
    if payload is None:
        return HttpResponse(status=404)

    content_type, _ = mimetypes.guess_type(path)
    http_response = HttpResponse(payload, content_type=content_type or "image/png")
    http_response["Cache-Control"] = "public, max-age=86400"
    http_response["Access-Control-Allow-Origin"] = "*"
    return http_response


HYPIXEL_PROFILES_URL = 'https://api.hypixel.net/v2/skyblock/profiles'
HYPIXEL_PLAYER_URL = 'https://api.hypixel.net/v2/player'
HYPIXEL_AUCTION_URL = 'https://api.hypixel.net/v2/skyblock/auction'
HYPIXEL_MUSEUM_URL = 'https://api.hypixel.net/v2/skyblock/museum'
HYPIXEL_PROFILES_CACHE_SECONDS = _read_int_env('HYPIXEL_PROFILES_CACHE_SECONDS', 20)
HYPIXEL_PLAYER_CACHE_SECONDS = _read_int_env('HYPIXEL_PLAYER_CACHE_SECONDS', 120)
HYPIXEL_AUCTION_CACHE_SECONDS = _read_int_env('HYPIXEL_AUCTION_CACHE_SECONDS', 60)
HYPIXEL_MUSEUM_CACHE_SECONDS = _read_int_env('HYPIXEL_MUSEUM_CACHE_SECONDS', 60)


def _fetch_hypixel_profiles(
    uuid: str, *, force_refresh: bool = False
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    cache_key = f'hypixel_profiles:{uuid}'
    if not force_refresh and HYPIXEL_PROFILES_CACHE_SECONDS > 0:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached, None

    api_key = os.getenv('HYPIXEL_API_KEY')
    if not api_key:
        return None, {'error': 'hypixel_api_key_missing', 'status': 503, 'fatal': False}

    try:
        response = _SESSION.get(
            HYPIXEL_PROFILES_URL,
            params={'uuid': uuid},
            headers={'API-Key': api_key},
            timeout=12,
        )
    except requests.RequestException as exc:
        return None, {'error': 'hypixel_request_failed', 'detail': str(exc), 'status': 502, 'fatal': True}

    if response.status_code == 429:
        return None, {'error': 'rate_limited', 'status': 429, 'fatal': False}

    if response.status_code == 403:
        cause: Optional[str] = None
        try:
            data = response.json()
            if isinstance(data, dict):
                raw_cause = data.get('cause') or data.get('message')
                if isinstance(raw_cause, str) and raw_cause.strip():
                    cause = raw_cause.strip()
        except ValueError:
            cause = None

        return None, {
            'error': 'hypixel_forbidden',
            'status': 503,
            'detail': cause
            or 'Hypixel API rejected the configured API key. Check HYPIXEL_API_KEY and Hypixel API access.',
            'fatal': True,
        }

    if response.status_code != 200:
        detail: str
        try:
            body = response.json()
            if isinstance(body, dict):
                detail = (
                    str(body.get('cause') or body.get('message') or body)
                )
            else:
                detail = str(body)
        except ValueError:
            detail = response.text

        if len(detail) > 2000:
            detail = detail[:2000] + '…'

        return None, {
            'error': 'hypixel_http_error',
            'status': response.status_code,
            'detail': detail,
            'fatal': True,
        }

    body = response.json()
    if body.get('success') is False:
        return None, {'error': 'hypixel_error', 'detail': body, 'status': 502, 'fatal': True}

    profiles = body.get('profiles') or []
    if not profiles:
        return None, {'error': 'no_profiles', 'status': 404, 'fatal': False}

    if HYPIXEL_PROFILES_CACHE_SECONDS > 0:
        cache.set(cache_key, body, HYPIXEL_PROFILES_CACHE_SECONDS)

    return body, None


def _fetch_player_achievements(uuid: str, *, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    api_key = os.getenv('HYPIXEL_API_KEY')
    if not api_key:
        return None

    cache_key = (
        f'hypixel_player_achievements:{uuid}' if HYPIXEL_PLAYER_CACHE_SECONDS > 0 else None
    )
    if cache_key and not force_refresh:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    try:
        response = _SESSION.get(
            HYPIXEL_PLAYER_URL,
            params={'uuid': uuid},
            headers={'API-Key': api_key},
            timeout=8,
        )
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    player_body = response.json() or {}
    if not player_body.get('success') or not isinstance(player_body.get('player'), dict):
        return None

    achievements = player_body['player'].get('achievements') or {}
    if cache_key:
        cache.set(cache_key, achievements, HYPIXEL_PLAYER_CACHE_SECONDS)
    return achievements


def _get_player_lookup_result(name: str, *, force_refresh: bool = False) -> Tuple[Dict[str, Any], int]:
    trimmed = (name or '').strip()
    if not trimmed or len(trimmed) > 16:
        return ({'error': 'invalid_username', 'message': 'Invalid username length'}, 400)

    identifier = trimmed.replace('_', '')
    if not identifier.isalnum():
        return ({'error': 'invalid_username', 'message': 'Username contains invalid characters'}, 400)

    normalized = trimmed.lower()
    cache_key = f'uuid:{normalized}'

    try:
        uuid = cache.get(cache_key)

        if not uuid:
            try:
                result = _SESSION.get(
                    f'https://api.mojang.com/users/profiles/minecraft/{normalized}',
                    timeout=5,
                )

                if result.status_code in (204, 404):
                    return (
                        {
                            'error': 'player_not_found',
                            'message': f'Player {normalized} not found',
                        },
                        404,
                    )

                result.raise_for_status()
                data = result.json()

                if not data or 'id' not in data:
                    return (
                        {
                            'error': 'invalid_response',
                            'message': 'Invalid response from Mojang API',
                        },
                        502,
                    )

                uuid = data['id']
                cache.set(cache_key, uuid, 3600)

            except requests.Timeout:
                return (
                    {'error': 'timeout', 'message': 'Mojang API request timed out'},
                    504,
                )
            except requests.RequestException as exc:
                return (
                    {'error': 'request_failed', 'message': str(exc)},
                    502,
                )
            except (ValueError, KeyError) as exc:
                return (
                    {
                        'error': 'parse_error',
                        'message': f'Failed to parse Mojang API response: {str(exc)}',
                    },
                    502,
                )

        body, error = _fetch_hypixel_profiles(uuid, force_refresh=force_refresh)
        if error:
            detail = error.get('detail')
            payload: Dict[str, Any] = {
                'name': normalized,
                'uuid': uuid,
                'profiles': None,
                'error': error.get('error'),
                'message': detail if isinstance(detail, str) else error.get('error'),
            }
            if detail is not None:
                payload['error_detail'] = detail
            if 'status' in error:
                payload['error_status'] = error['status']

            status_code = error.get('status') or (502 if error.get('fatal') else 200)
            return payload, status_code

        raw_profiles = body.get('profiles') or []
        profiles = []
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        for raw in raw_profiles:
            members = raw.get('members') or {}

            member_count = count_coop_members(members, now_ms=now_ms)

            profiles.append(
                {
                    'profile_id': raw.get('profile_id') or raw.get('uuid'),
                    'cute_name': raw.get('cute_name'),
                    'name': raw.get('name'),
                    'game_mode': raw.get('game_mode'),
                    'last_save': raw.get('last_save'),
                    'last_save_iso': raw.get('last_save_iso') or raw.get('lastSaveIso'),
                    'member_count': member_count,
                }
            )

        payload = {
            'name': normalized,
            'uuid': uuid,
            'profiles': profiles,
            'last_updated': body.get('last_updated') or body.get('lastUpdated'),
        }
        return payload, 200

    except Exception as exc:  # pragma: no cover - defensive
        return (
            {
                'error': 'server_error',
                'message': f'An unexpected error occurred: {str(exc)}',
            },
            500,
        )


def _fetch_museum_data(
    profile_id: str, *, force_refresh: bool = False
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Fetch museum data for a profile from Hypixel API.
    """
    cache_key = f'hypixel_museum:{profile_id}'
    if not force_refresh and HYPIXEL_MUSEUM_CACHE_SECONDS > 0:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached, None

    api_key = os.getenv('HYPIXEL_API_KEY')
    if not api_key:
        return None, {'error': 'hypixel_api_key_missing', 'status': 503, 'fatal': False}

    try:
        response = _SESSION.get(
            HYPIXEL_MUSEUM_URL,
            params={'profile': profile_id},
            headers={'API-Key': api_key},
            timeout=12,
        )
    except requests.RequestException as exc:
        return None, {'error': 'hypixel_request_failed', 'detail': str(exc), 'status': 502, 'fatal': True}

    if response.status_code == 429:
        return None, {'error': 'rate_limited', 'status': 429, 'fatal': False}

    if response.status_code == 403:
        cause: Optional[str] = None
        try:
            data = response.json()
            if isinstance(data, dict):
                raw_cause = data.get('cause') or data.get('message')
                if isinstance(raw_cause, str) and raw_cause.strip():
                    cause = raw_cause.strip()
        except ValueError:
            cause = None

        return None, {
            'error': 'hypixel_forbidden',
            'status': 503,
            'detail': cause or 'Hypixel API rejected the request.',
            'fatal': True,
        }

    if response.status_code != 200:
        detail: str
        try:
            body = response.json()
            if isinstance(body, dict):
                detail = str(body.get('cause') or body.get('message') or body)
            else:
                detail = str(body)
        except ValueError:
            detail = response.text

        if len(detail) > 2000:
            detail = detail[:2000] + '…'

        return None, {
            'error': 'hypixel_http_error',
            'status': response.status_code,
            'detail': detail,
            'fatal': True,
        }

    body = response.json()

    if HYPIXEL_MUSEUM_CACHE_SECONDS > 0:
        cache.set(cache_key, body, HYPIXEL_MUSEUM_CACHE_SECONDS)

    return body, None


def _fetch_player_auctions(
    uuid: str, *, force_refresh: bool = False
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
    """
    Fetch active auctions for a player from Hypixel API.
    """
    cache_key = f'hypixel_auctions:{uuid}'
    if not force_refresh and HYPIXEL_AUCTION_CACHE_SECONDS > 0:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached, None

    api_key = os.getenv('HYPIXEL_API_KEY')
    if not api_key:
        return None, {'error': 'hypixel_api_key_missing', 'status': 503, 'fatal': False}

    try:
        response = _SESSION.get(
            HYPIXEL_AUCTION_URL,
            params={'player': uuid},
            headers={'API-Key': api_key},
            timeout=12,
        )
    except requests.RequestException as exc:
        return None, {'error': 'hypixel_request_failed', 'detail': str(exc), 'status': 502, 'fatal': True}

    if response.status_code == 429:
        return None, {'error': 'rate_limited', 'status': 429, 'fatal': False}

    if response.status_code == 403:
        cause: Optional[str] = None
        try:
            data = response.json()
            if isinstance(data, dict):
                raw_cause = data.get('cause') or data.get('message')
                if isinstance(raw_cause, str) and raw_cause.strip():
                    cause = raw_cause.strip()
        except ValueError:
            cause = None

        return None, {
            'error': 'hypixel_forbidden',
            'status': 503,
            'detail': cause or 'Hypixel API rejected the request.',
            'fatal': True,
        }

    if response.status_code != 200:
        detail: str
        try:
            body = response.json()
            if isinstance(body, dict):
                detail = str(body.get('cause') or body.get('message') or body)
            else:
                detail = str(body)
        except ValueError:
            detail = response.text

        if len(detail) > 2000:
            detail = detail[:2000] + '…'

        return None, {
            'error': 'hypixel_http_error',
            'status': response.status_code,
            'detail': detail,
            'fatal': True,
        }

    body = response.json()
    if body.get('success') is False:
        return None, {'error': 'hypixel_error', 'detail': body, 'status': 502, 'fatal': True}

    auctions = body.get('auctions') or []
    
    # Enrich auctions with parsed item data
    enriched_auctions = []
    for auction in auctions:
        enriched = _enrich_auction_item(auction)
        enriched_auctions.append(enriched)

    if HYPIXEL_AUCTION_CACHE_SECONDS > 0:
        cache.set(cache_key, enriched_auctions, HYPIXEL_AUCTION_CACHE_SECONDS)

    return enriched_auctions, None


def _enrich_auction_item(auction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse auction item_bytes to extract icon information.
    """
    result = dict(auction)
    item_bytes = auction.get('item_bytes')
    if not item_bytes:
        return result
    
    # Handle item_bytes as object with 'data' field or direct string
    if isinstance(item_bytes, dict):
        item_bytes_str = item_bytes.get('data')
    else:
        item_bytes_str = item_bytes
    
    if not item_bytes_str:
        return result
    
    # Use centralized parsing logic from wardrobe
    # This handles NBT decoding, texture resolution, and color parsing consistently
    parsed_items = _parse_inventory_items({'data': item_bytes_str})
    
    if not parsed_items or not parsed_items[0]:
        return result
        
    item = parsed_items[0]
    
    result['skyblock_id'] = item.get('id')
    result['mc_id'] = item.get('mc_id')
    result['icon_url'] = item.get('icon_url')
    result['icon_variants'] = item.get('icon_variants')
    result['leather_color'] = item.get('leather_color')
    result['lore'] = item.get('lore')
    result['lore_colored'] = item.get('lore_colored')
    
    return result


@api_view(['GET'])
def health(_: Request) -> Response:
    return Response({'ok': True})


@api_view(['GET'])
def player_lookup(request: Request, name: str) -> Response:
    force_refresh = _should_bypass_cache(getattr(request, 'query_params', None))
    payload, status_code = _get_player_lookup_result(name, force_refresh=force_refresh)
    return Response(payload, status=status_code)


@api_view(['GET'])
def hypixel_profile(request: Request, uuid: str) -> Response:
    """
    Raw SkyBlock profile list from Hypixel for the given Minecraft UUID.
    """
    force_refresh = _should_bypass_cache(getattr(request, 'query_params', None))
    body, error = _fetch_hypixel_profiles(uuid, force_refresh=force_refresh)
    if error:
        payload = {'error': error.get('error')}
        if 'detail' in error:
            payload['detail'] = error['detail']
        return Response(payload, status=error.get('status') or 502)
    return Response(body)


@api_view(['GET'])
def hypixel_player_auctions(request: Request, uuid: str) -> Response:
    """
    Active auctions for a player from Hypixel SkyBlock.
    """
    force_refresh = _should_bypass_cache(getattr(request, 'query_params', None))
    auctions, error = _fetch_player_auctions(uuid, force_refresh=force_refresh)
    if error:
        payload = {'error': error.get('error')}
        if 'detail' in error:
            payload['detail'] = error['detail']
        return Response(payload, status=error.get('status') or 502)
    return Response({'auctions': auctions or []})
    if error:
        payload = {'error': error.get('error')}
        if 'detail' in error:
            payload['detail'] = error['detail']
        return Response(payload, status=error.get('status') or 502)
    return Response(body)


@api_view(['GET'])
def hypixel_profile_summary(request: Request, uuid: str, profile_id: str) -> Response:
    """
    Enriched summary for a specific profile belonging to the given UUID.
    """
    force_refresh = _should_bypass_cache(getattr(request, 'query_params', None))
    body, error = _fetch_hypixel_profiles(uuid, force_refresh=force_refresh)
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

    # Hypixel member keys are UUIDs without dashes; normalize for lookup
    normalized_member_uuid = (uuid or "").replace("-", "")

    # Fetch player achievements from Hypixel main player endpoint to align with SkyCrypt logic
    achievements = _fetch_player_achievements(uuid, force_refresh=force_refresh)

    if force_refresh:
        summary = summarize_profile(normalized_member_uuid, target, achievements=achievements)
    else:
        summary = get_cached_profile_summary(normalized_member_uuid, target, achievements=achievements)

    if not summary:
        return Response({'error': 'member_not_in_profile'}, status=404)

    computed_stats = None
    # 원본 member 데이터를 함께 전달
    member_data = target.get('members', {}).get(normalized_member_uuid)
    
    # skip_stats 파라미터 확인
    skip_stats = _is_truthy(request.query_params.get('skip_stats'))
    
    stat_breakdown = None
    weapon_slot = None
    raw_weapon_slot = request.query_params.get('weapon_slot')
    if raw_weapon_slot is not None:
        try:
            weapon_slot = int(raw_weapon_slot)
        except (TypeError, ValueError):
            weapon_slot = None
        else:
            if weapon_slot < 0 or weapon_slot > 8:
                weapon_slot = None
    raw_weapon_id = request.query_params.get('weapon_id')
    weapon_id = raw_weapon_id.strip() if isinstance(raw_weapon_id, str) else None
    if weapon_id == "":
        weapon_id = None
    if weapon_id:
        weapon_id = weapon_id.strip().upper().replace(" ", "_").replace("-", "_")
        while "__" in weapon_id:
            weapon_id = weapon_id.replace("__", "_")
    if not skip_stats:
        # LOGGER.warning(f"Building statscalc payload for weapon_slot={weapon_slot}, weapon_id={weapon_id}")
        stats_payload = _build_statscalc_payload(
            summary,
            normalized_member_uuid,
            profile_id,
            member_data,
            weapon_slot=weapon_slot,
            weapon_id=weapon_id,
        )
        if stats_payload:
            # LOGGER.warning("Calling statscalc_client.calculate_stats")
            calc_result = statscalc_client.calculate_stats(stats_payload)
            if calc_result:
                stats_block = calc_result.get('stats')
                if isinstance(stats_block, dict) and 'stats' in stats_block:
                    computed_stats = stats_block
                else:
                    computed_stats = {
                        'stats': stats_block or {},
                        'breakdown': calc_result.get('breakdown') or {},
                    }
                stat_breakdown = computed_stats.get('breakdown')

    response_body = {
        'ok': True,
        'last_updated': body.get('last_updated') or body.get('lastUpdated'),
        **summary,
    }
    if member_data:
        from .domain.nbt_parser import extract_weapon_candidates_from_profile, extract_weapon_from_profile, extract_pets_from_profile

        weapon_candidates = extract_weapon_candidates_from_profile(member_data)
        if weapon_candidates:
            response_body['weapon_candidates'] = weapon_candidates
            selected_weapon = extract_weapon_from_profile(member_data, preferred_slot=weapon_slot)
            if selected_weapon:
                response_body['weapon_selected_slot'] = selected_weapon.get('slot')
        
        # Always include weapon catalog
        response_body['weapon_catalog'] = _load_weapon_catalog()
        if weapon_id:
            response_body['weapon_selected_id'] = weapon_id
        
        # Extract pets data for frontend
        pets = extract_pets_from_profile(member_data)
        if pets:
            response_body['pets'] = pets
            response_body['pet_score'] = _calculate_pet_score(pets)
    if computed_stats:
        response_body['computed_stats'] = computed_stats
    if stat_breakdown:
        response_body['stat_breakdown'] = stat_breakdown

    # Museum 데이터 지연 로딩: skip_museum=1이면 museum API 호출 생략
    # SSR에서는 skip_museum=1로 빠른 초기 렌더링, 클라이언트에서 별도 요청
    skip_museum = _is_truthy(request.query_params.get('skip_museum'))
    if not skip_museum:
        # Fetch museum data
        museum_body, museum_error = _fetch_museum_data(profile_id, force_refresh=force_refresh)
        if museum_body and not museum_error:
            museum_members = museum_body.get('members') or {}
            
            # Fetch prices for networth calculation
            from .domain.networth import fetch_prices
            prices = fetch_prices()
            
            parsed_museum = parse_museum(museum_members, normalized_member_uuid, prices)
            if parsed_museum:
                museum_summary = get_museum_summary(parsed_museum)
                # Add missing items with prices
                missing_items = get_missing_items(parsed_museum, include_prices=True, sort_by_price=True)
                museum_summary['missing'] = missing_items
                response_body['museum'] = museum_summary
                
                # Use calculated value from museum summary
                museum_value = museum_summary.get('calculated_value', 0)
                
                # Fallback to Hypixel base value if calculated is 0
                if museum_value <= 0:
                     museum_value = museum_summary.get('value', 0)
                
                if museum_value and response_body.get('networth'):
                    nw = response_body['networth']
                    # Only add if not already present (e.g. from SkyHelper API)
                    if 'categories' in nw and 'museum' not in nw['categories']:
                        nw['total'] = nw.get('total', 0) + museum_value
                        # Museum items are soulbound, so they don't add to unsoulbound
                        nw['categories']['museum'] = {
                            'name': 'Museum',
                            'total': museum_value
                        }
            else:
                response_body['museum'] = {'available': False}
        else:
            response_body['museum'] = {'available': False}
    else:
        response_body['museum'] = {'deferred': True}

    return Response(response_body)


@api_view(['GET'])
def hypixel_profile_summary_by_name(request: Request, name: str, profile_id: str) -> Response:
    """
    Enriched summary for a specific profile using player name instead of UUID.
    This eliminates the need for a separate player lookup call, improving page load speed.
    """
    force_refresh = _should_bypass_cache(getattr(request, 'query_params', None))
    
    # Resolve name to UUID first
    player_result, status_code = _get_player_lookup_result(name, force_refresh=force_refresh)
    if status_code != 200 or 'uuid' not in player_result:
        return Response(player_result, status=status_code)
    
    uuid = player_result['uuid']
    player_name = player_result.get('name', name)
    
    # Reuse the existing logic from hypixel_profile_summary
    body, error = _fetch_hypixel_profiles(uuid, force_refresh=force_refresh)
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

    normalized_member_uuid = (uuid or "").replace("-", "")
    achievements = _fetch_player_achievements(uuid, force_refresh=force_refresh)

    summary = summarize_profile(normalized_member_uuid, target, achievements=achievements)
    if not summary:
        return Response({'error': 'member_not_in_profile'}, status=404)
    
    LOGGER.warning(f"[DEBUG] summary keys: {list(summary.keys())}")
    LOGGER.warning(f"[DEBUG] 'museum' in summary: {'museum' in summary}")

    member_data = target.get('members', {}).get(normalized_member_uuid)
    skip_stats = _is_truthy(request.query_params.get('skip_stats'))
    
    computed_stats = None
    stat_breakdown = None
    weapon_slot = None
    raw_weapon_slot = request.query_params.get('weapon_slot')
    if raw_weapon_slot is not None:
        try:
            weapon_slot = int(raw_weapon_slot)
        except (TypeError, ValueError):
            weapon_slot = None
        else:
            if weapon_slot < 0 or weapon_slot > 8:
                weapon_slot = None
    raw_weapon_id = request.query_params.get('weapon_id')
    weapon_id = raw_weapon_id.strip() if isinstance(raw_weapon_id, str) else None
    if weapon_id == "":
        weapon_id = None
    if weapon_id:
        weapon_id = weapon_id.strip().upper().replace(" ", "_").replace("-", "_")
        while "__" in weapon_id:
            weapon_id = weapon_id.replace("__", "_")
    
    if not skip_stats:
        stats_payload = _build_statscalc_payload(
            summary,
            normalized_member_uuid,
            profile_id,
            member_data,
            weapon_slot=weapon_slot,
            weapon_id=weapon_id,
        )
        if stats_payload:
            calc_result = statscalc_client.calculate_stats(stats_payload)
            if calc_result:
                stats_block = calc_result.get('stats')
                if isinstance(stats_block, dict) and 'stats' in stats_block:
                    computed_stats = stats_block
                else:
                    computed_stats = {
                        'stats': stats_block or {},
                        'breakdown': calc_result.get('breakdown') or {},
                    }
                stat_breakdown = computed_stats.get('breakdown')

    response_body = {
        'ok': True,
        'player': {'name': player_name, 'uuid': uuid},
        'last_updated': body.get('last_updated') or body.get('lastUpdated'),
        **summary,
    }
    
    if member_data:
        from .domain.nbt_parser import extract_weapon_candidates_from_profile, extract_weapon_from_profile, extract_pets_from_profile

        weapon_candidates = extract_weapon_candidates_from_profile(member_data)
        if weapon_candidates:
            response_body['weapon_candidates'] = weapon_candidates
            selected_weapon = extract_weapon_from_profile(member_data, preferred_slot=weapon_slot)
            if selected_weapon:
                response_body['weapon_selected_slot'] = selected_weapon.get('slot')
        
        # Always include weapon catalog
        response_body['weapon_catalog'] = _load_weapon_catalog()
        if weapon_id:
            response_body['weapon_selected_id'] = weapon_id
        
        pets = extract_pets_from_profile(member_data)
        if pets:
            response_body['pets'] = pets
            response_body['pet_score'] = _calculate_pet_score(pets)
    
    if computed_stats:
        response_body['computed_stats'] = computed_stats
    if stat_breakdown:
        response_body['stat_breakdown'] = stat_breakdown

    # Museum 데이터 지연 로딩
    skip_museum = _is_truthy(request.query_params.get('skip_museum'))
    LOGGER.warning(f"[DEBUG] skip_museum: {skip_museum}")
    if not skip_museum:
        museum_body, museum_error = _fetch_museum_data(profile_id, force_refresh=force_refresh)
        LOGGER.warning(f"[DEBUG] museum_body: {museum_body is not None}, museum_error: {museum_error}")
        if museum_body and not museum_error:
            museum_members = museum_body.get('members') or {}
            LOGGER.warning(f"[DEBUG] Museum members keys: {list(museum_members.keys())}")
            LOGGER.warning(f"[DEBUG] Normalized UUID: {normalized_member_uuid}")
            parsed_museum = get_cached_museum_summary(normalized_member_uuid, museum_members, force_refresh=force_refresh)
            LOGGER.warning(f"[DEBUG] Parsed museum: {parsed_museum is not None}")
            if parsed_museum:
                LOGGER.warning(f"[DEBUG] Parsed museum value: {parsed_museum.get('value', 'NO_VALUE')}")
                museum_summary = get_museum_summary(parsed_museum)
                LOGGER.warning(f"[DEBUG] Museum summary value: {museum_summary.get('value', 'NO_VALUE')}")
                missing_items = get_missing_items(parsed_museum, include_prices=True, sort_by_price=True)
                museum_summary['missing'] = missing_items
                response_body['museum'] = museum_summary
                
                # Calculate actual museum value with modifiers (enchants, stars, HPB, etc.)
                # Hypixel's museum value only counts base item prices
                from .domain.networth import calculate_items_value, fetch_prices, _parse_inventory_items
                
                # Initialize with Hypixel's base value
                museum_value = museum_summary.get('value', 0)
                LOGGER.warning(f"[DEBUG] Initial museum_value from summary: {museum_value:,.0f}")
                
                try:
                    prices = fetch_prices()
                    museum_items_data = []
                    
                    # Extract museum items from API response
                    member_museum = museum_members.get(normalized_member_uuid) or museum_members.get(normalized_member_uuid.replace("-", ""))
                    if member_museum:
                        raw_items = member_museum.get("items", {})
                        raw_list = raw_items.values() if isinstance(raw_items, dict) else (raw_items if isinstance(raw_items, list) else [])

                        def _maybe_add(blob):
                            if isinstance(blob, str) and blob:
                                return [blob]
                            return []

                        for item_entry in raw_list:
                            if not isinstance(item_entry, dict):
                                continue
                            candidates = []
                            candidates += _maybe_add(item_entry.get("data"))
                            candidates += _maybe_add(item_entry.get("item_data") or item_entry.get("itemData") or item_entry.get("itemBytes"))
                            items_data = item_entry.get("items")
                            if isinstance(items_data, dict):
                                candidates += _maybe_add(items_data.get("data"))
                            elif isinstance(items_data, list):
                                for sub in items_data:
                                    if isinstance(sub, dict):
                                        candidates += _maybe_add(sub.get("data"))

                            for raw_data in candidates:
                                try:
                                    parsed_items = _parse_inventory_items({'data': raw_data})
                                    museum_items_data.extend(parsed_items)
                                except Exception as e:
                                    LOGGER.debug(f"Failed to parse museum item: {e}")
                    
                    # Calculate actual value with all modifiers
                    LOGGER.warning(f"[DEBUG] museum_items_data count: {len(museum_items_data)}")
                    if museum_items_data:
                        museum_value, _, _ = calculate_items_value(museum_items_data, prices)
                        LOGGER.warning(f"Museum actual value with modifiers: {museum_value:,.0f} (Hypixel base: {museum_summary.get('value', 0):,.0f})")
                        if museum_value <= 0:
                            LOGGER.warning("Museum computed as 0; falling back to Hypixel base value")
                            museum_value = museum_summary.get('value', 0)
                    else:
                        LOGGER.warning(f"Using Hypixel base museum value (no items data): {museum_value:,.0f}")
                except Exception as e:
                    LOGGER.warning(f"Failed to calculate actual museum value: {e}, using base value: {museum_value:,.0f}")
                
                LOGGER.warning(f"[DEBUG] Final museum_value: {museum_value:,.0f}")
                if museum_value and response_body.get('networth'):
                    LOGGER.warning(f"[DEBUG] Adding museum to networth")
                    nw = response_body['networth']
                    nw['total'] = nw.get('total', 0) + museum_value
                    if 'categories' in nw:
                        nw['categories']['museum'] = {
                            'name': 'Museum',
                            'total': museum_value
                        }
                else:
                    LOGGER.warning(f"[DEBUG] NOT adding museum: museum_value={museum_value}, has_networth={response_body.get('networth') is not None}")
            else:
                LOGGER.warning(f"[DEBUG] Setting museum unavailable (parsed_museum is None)")
                response_body['museum'] = {'available': False}
        else:
            LOGGER.warning(f"[DEBUG] Setting museum unavailable (museum_body or museum_error issue)")
            response_body['museum'] = {'available': False}
    else:
        LOGGER.warning(f"[DEBUG] Skipping museum (skip_museum=True)")
        response_body['museum'] = {'deferred': True}
    
    LOGGER.warning(f"[DEBUG] Final response_body museum value: {response_body.get('museum', {}).get('value', 'NO_VALUE')}")
    return Response(response_body)


FONT_CANDIDATES = {
    'regular': [
        '/usr/share/fonts/truetype/inter/Inter-Regular.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/Library/Fonts/Arial.ttf',
        'C:/Windows/Fonts/arial.ttf',
        'arial.ttf',
    ],
    'semibold': [
        '/usr/share/fonts/truetype/inter/Inter-SemiBold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/Library/Fonts/Arial Bold.ttf',
        'C:/Windows/Fonts/arialbd.ttf',
        'arialbd.ttf',
    ],
}


def _load_font(size: int, weight: str = 'regular') -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES.get(weight, []):
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _format_relative_timestamp(value: Optional[Any]) -> str:
    if value is None:
        return 'Unknown'
    try:
        raw = float(value)
    except (TypeError, ValueError):
        try:
            raw = float(str(value))
        except ValueError:
            return 'Unknown'

    if raw > 1_000_000_000_000:
        raw = raw / 1000.0
    elif raw > 1_000_000_000:
        raw = raw / 1000.0

    try:
        timestamp = datetime.fromtimestamp(raw, tz=timezone.utc)
    except (ValueError, OSError):
        return 'Unknown'

    delta = datetime.now(timezone.utc) - timestamp
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return 'just now'
    minutes = seconds // 60
    if minutes < 60:
        return f'{minutes}m ago'
    hours = minutes // 60
    if hours < 24:
        return f'{hours}h ago'
    days = hours // 24
    if days < 30:
        return f'{days}d ago'
    months = days // 30
    if months < 12:
        return f'{months}mo ago'
    years = months // 12
    return f'{years}y ago'


def _format_last_updated(value: Optional[Any]) -> str:
    if not value:
        return 'Cache: n/a'

    if isinstance(value, (int, float)):
        return f'Cache: {_format_relative_timestamp(value)}'

    if isinstance(value, str):
        sample = value.strip()
        if sample.isdigit():
            return f'Cache: {_format_relative_timestamp(int(sample))}'
        try:
            dt = datetime.fromisoformat(sample.replace('Z', '+00:00'))
            delta = datetime.now(timezone.utc) - dt
            minutes = int(delta.total_seconds() // 60)
            if minutes < 60:
                return f'Cache: {minutes}m ago'
            hours = minutes // 60
            if hours < 24:
                return f'Cache: {hours}h ago'
            days = hours // 24
            return f'Cache: {days}d ago'
        except ValueError:
            return f'Cache: {sample}'

    return 'Cache: n/a'


_WEAPON_CATALOG: Optional[List[Dict[str, str]]] = None


def _format_weapon_name(item_id: str) -> str:
    normalized = item_id.strip().replace("_", " ").strip()
    if not normalized:
        return item_id
    return " ".join(part[:1].upper() + part[1:].lower() for part in normalized.split())


def _load_weapon_catalog() -> List[Dict[str, str]]:
    global _WEAPON_CATALOG
    if _WEAPON_CATALOG is not None:
        return _WEAPON_CATALOG

    stats_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "statscalc", "data", "stats")
    )
    candidates: Dict[str, str] = {}
    for filename in ("weapons_wiki.json", "weapons.json"):
        path = os.path.join(stats_dir, filename)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            continue
        weapon_stats = data.get("weapon_stats")
        if not isinstance(weapon_stats, dict):
            continue
        for item_id in weapon_stats.keys():
            if not isinstance(item_id, str):
                continue
            candidates[item_id] = _format_weapon_name(item_id)

    catalog = [
        {"id": item_id, "name": name}
        for item_id, name in sorted(candidates.items(), key=lambda item: item[1])
    ]
    _WEAPON_CATALOG = catalog
    return catalog


def _normalize_tuning_map(raw: Any) -> Dict[str, int]:
    result: Dict[str, int] = {}
    allowed_stats = {
        "health",
        "defense",
        "walk_speed",
        "speed",
        "strength",
        "critical_damage",
        "crit_damage",
        "critical_chance",
        "crit_chance",
        "attack_speed",
        "bonus_attack_speed",
        "intelligence",
    }
    if isinstance(raw, dict):
        slot_entries = {
            int(key.split("_", 1)[1]): value
            for key, value in raw.items()
            if isinstance(key, str)
            and key.startswith("slot_")
            and key.split("_", 1)[1].isdigit()
            and isinstance(value, dict)
        }
        if slot_entries:
            selected = raw.get("selected_slot") or raw.get("selected") or raw.get("active_slot") or raw.get("current_slot") or raw.get("slot")
            selected_slot = None
            if selected is not None:
                try:
                    selected_slot = int(float(selected))
                except (TypeError, ValueError):
                    selected_slot = None
            if selected_slot is not None and selected_slot in slot_entries:
                chosen = slot_entries[selected_slot]
            else:
                non_zero_slots = []
                for slot_id, entry in slot_entries.items():
                    for _, value in entry.items():
                        try:
                            parsed = int(float(value))
                        except (TypeError, ValueError):
                            continue
                        if parsed != 0:
                            non_zero_slots.append(slot_id)
                            break
                if len(non_zero_slots) == 1:
                    chosen = slot_entries[non_zero_slots[0]]
                else:
                    chosen = slot_entries.get(0) or next(iter(slot_entries.values()))

            for key, value in chosen.items():
                if str(key) not in allowed_stats:
                    continue
                try:
                    parsed = int(float(value))
                except (TypeError, ValueError):
                    continue
                if parsed != 0:
                    result[str(key)] = result.get(str(key), 0) + parsed
            return result
        for key, value in raw.items():
            if str(key) not in allowed_stats:
                continue
            try:
                parsed = int(float(value))
            except (TypeError, ValueError):
                continue
            if parsed != 0:
                result[str(key)] = parsed
        return result
    if isinstance(raw, list):
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            key = entry.get("stat") or entry.get("key") or entry.get("name")
            if not key:
                continue
            if str(key) not in allowed_stats:
                continue
            value = entry.get("value") if "value" in entry else entry.get("points")
            try:
                parsed = int(float(value))
            except (TypeError, ValueError):
                continue
            if parsed != 0:
                result[str(key)] = parsed
    return result


def _find_tuning_map(container: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(container, dict):
        return None
    tuning = container.get("tuning")
    if isinstance(tuning, dict):
        return tuning
    for key in ("bag_data", "bag", "inventory", "contents"):
        nested = container.get(key)
        if isinstance(nested, dict):
            nested_tuning = nested.get("tuning")
            if isinstance(nested_tuning, dict):
                return nested_tuning
    return None


def _extract_accessory_tuning(member_data: Dict[str, Any]) -> Dict[str, int]:
    if not isinstance(member_data, dict):
        return {}
    inventory = member_data.get("inventory") or {}
    bag_contents = inventory.get("bag_contents") if isinstance(inventory, dict) else None
    candidates = [
        member_data.get("accessory_bag_storage"),
        member_data.get("talisman_bag_storage"),
        inventory.get("accessory_bag_storage") if isinstance(inventory, dict) else None,
        inventory.get("talisman_bag_storage") if isinstance(inventory, dict) else None,
        bag_contents.get("talisman_bag") if isinstance(bag_contents, dict) else None,
        inventory.get("accessory_bag") if isinstance(inventory, dict) else None,
        inventory.get("talisman_bag") if isinstance(inventory, dict) else None,
        member_data.get("accessory_bag"),
        member_data.get("talisman_bag"),
    ]
    for candidate in candidates:
        tuning = _find_tuning_map(candidate)
        normalized = _normalize_tuning_map(tuning)
        if normalized:
            return normalized
    return {}


def _calculate_pet_score(pets: List[Dict[str, Any]]) -> int:
    """Calculate pet score based on SkyCrypt logic.
    
    Pet score = sum of highest rarity per pet type + 1 for each maxed unique pet type
    
    Rarity scores: COMMON=1, UNCOMMON=2, RARE=3, EPIC=4, LEGENDARY=5, MYTHIC=6
    Max level bonus: +1 per unique pet type that has reached max level
    
    Special cases:
    - GOLDEN_DRAGON max level is 200
    - FRACTURED_MONTEZUMA_SOUL is ignored in calculation
    """
    # Pet type -> max level mapping (default 100)
    PET_MAX_LEVELS = {
        'GOLDEN_DRAGON': 200,
    }
    
    # Pets to ignore in score calculation
    IGNORED_PETS = {'FRACTURED_MONTEZUMA_SOUL'}
    
    highest_rarity: Dict[str, int] = {}
    has_max_level: Dict[str, bool] = {}
    
    rarity_score = {
        'COMMON': 1,
        'UNCOMMON': 2,
        'RARE': 3,
        'EPIC': 4,
        'LEGENDARY': 5,
        'MYTHIC': 6
    }
    
    for pet in pets:
        pet_type = pet.get('type')
        rarity = pet.get('tier')
        level = pet.get('level', 0)
        
        if not pet_type or not rarity:
            continue
            
        # Skip ignored pets
        if pet_type in IGNORED_PETS:
            continue
            
        # Track highest rarity per pet type
        score = rarity_score.get(rarity, 0)
        if score > highest_rarity.get(pet_type, 0):
            highest_rarity[pet_type] = score
        
        # Check if pet is at max level
        max_level = PET_MAX_LEVELS.get(pet_type, 100)
        if level >= max_level and not has_max_level.get(pet_type, False):
            has_max_level[pet_type] = True
    
    # Total score = rarity scores + max level bonuses
    rarity_total = sum(highest_rarity.values())
    max_level_bonus = sum(1 for v in has_max_level.values() if v)
    
    return rarity_total + max_level_bonus


def _build_statscalc_payload(
    summary: Dict[str, Any], 
    uuid: str, 
    profile_id: str,
    member_data: Optional[Dict[str, Any]] = None,
    weapon_slot: Optional[int] = None,
    weapon_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    if not summary:
        return None

    skills_payload: Dict[str, Dict[str, int]] = {}
    skills_block = summary.get('skills') or {}
    if isinstance(skills_block, dict):
        for key, data in skills_block.items():
            if not isinstance(data, dict):
                continue
            level = data.get('level')
            if not isinstance(level, (int, float)):
                continue
            payload_item = {'level': int(level)}
            xp = data.get('xp')
            if isinstance(xp, (int, float)):
                payload_item['xp'] = int(xp)
            skills_payload[key] = payload_item

    slayer_payload: Dict[str, Dict[str, int]] = {}
    slayer_block = summary.get('slayer') or {}
    if isinstance(slayer_block, dict):
        for key, data in slayer_block.items():
            if key == 'total_xp' or not isinstance(data, dict):
                continue
            level = data.get('level')
            if not isinstance(level, (int, float)):
                continue
            payload_item = {'level': int(level)}
            xp = data.get('xp')
            if isinstance(xp, (int, float)):
                payload_item['xp'] = int(xp)
            slayer_payload[key] = payload_item

    payload = {
        'uuid': uuid,
        'profile_id': profile_id,
        'skills': skills_payload,
        'slayer': slayer_payload,
    }
    
    # 확장: 장비, 악세서리, 펫, HOTM 데이터 추가
    if member_data:
        from .domain.nbt_parser import (
            extract_equipment_from_profile,
            extract_accessories_from_profile,
            extract_weapon_from_profile,
            extract_pets_from_profile,
            extract_hotm_from_profile,
            extract_dungeons_from_profile,
        )
        
        # 장비 (방어구)
        equipment_data = extract_equipment_from_profile(member_data)
        equipment_payload = {}
        for slot, item in equipment_data.items():
            if item:
                equipment_payload[slot] = _serialize_item(item)
        weapon_item = None
        if weapon_id:
            weapon_item = {'id': weapon_id}
        else:
            weapon_item = extract_weapon_from_profile(member_data, preferred_slot=weapon_slot)
        if weapon_item:
            equipment_payload['weapon'] = _serialize_item(weapon_item)
        if equipment_payload:
            payload['equipment'] = equipment_payload
        
        # 악세서리
        accessories = extract_accessories_from_profile(member_data)
        if accessories:
            payload['accessories'] = [_serialize_accessory(acc) for acc in accessories]
        
        # Selected Power (from summary if available, as nbt_parser doesn't extract it yet)
        if summary.get('accessories') and isinstance(summary['accessories'], dict):
            selected_power = summary['accessories'].get('selected_power')
            if selected_power:
                payload['selected_power'] = selected_power
            
            # Magical Power (from summary, which is more accurate)
            magical_power = summary['accessories'].get('magical_power')
            if magical_power:
                payload['magical_power'] = magical_power
            
            # Tuning Points
            tuning = summary['accessories'].get('tuning')
            if not tuning and member_data:
                tuning = _extract_accessory_tuning(member_data)
            if tuning:
                payload['tuning'] = tuning

        # 펫
        pets = extract_pets_from_profile(member_data)
        if pets:
            payload['pets'] = pets
            payload['pet_score'] = _calculate_pet_score(pets)
        
        # Collections - statscalc expects map[string]int, not the full processed structure
        raw_collections = member_data.get('collection', {})
        if raw_collections and isinstance(raw_collections, dict):
            # Ensure values are integers
            payload['collections'] = {k: int(v) for k, v in raw_collections.items() if isinstance(v, (int, float))}
        
        # HOTM
        hotm = extract_hotm_from_profile(member_data)
        if hotm:
            payload['hotm'] = hotm
            
        # SkyBlock Level
        leveling = member_data.get('leveling', {})
        if isinstance(leveling, dict):
            sb_xp = leveling.get('experience', 0)
            if sb_xp > 0:
                # Level = XP / 100
                payload['skyblock_level'] = int(sb_xp / 100)
        
        # Fairy Souls
        fairy_souls = member_data.get('fairy_souls_collected', 0)
        if fairy_souls:
            payload['fairy_souls'] = fairy_souls

        # Dungeons
        dungeons = extract_dungeons_from_profile(member_data)
        if dungeons:
            payload['dungeons'] = dungeons
    
    return payload if (skills_payload or slayer_payload) else None


def _serialize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """아이템 데이터를 statscalc payload 형식으로 변환"""
    extra = item.get('extra_attributes', {})
    result: Dict[str, Any] = {
        'id': extra.get('id') or item.get('id'),
    }
    
    if item.get('count'):
        result['count'] = item['count']
    if item.get('rarity'):
        result['rarity'] = item['rarity']
    if extra.get('reforge'):
        result['reforge'] = extra['reforge']
    if extra.get('enchants'):
        result['enchants'] = extra['enchants']
    if extra.get('hot_potato_count'):
        result['hot_potato_count'] = extra['hot_potato_count']
    if extra.get('gems'):
        # gems는 이제 {slot: {type, quality}} 형태
        result['gems'] = extra['gems']
    if extra.get('runes'):
        result['runes'] = extra['runes']
    if extra.get('stars'):
        result['stars'] = extra['stars']
    if extra.get('recombobulated'):
        result['recombobulated'] = extra['recombobulated']

    extra_payload = {}
    for key in (
        'attributes',
        'art_of_war_count',
        'ethermerge',
        'abiphone_contacts_count',
        'enderman_kills',
        'zombie_kills',
        'lore_stats',  # lore에서 파싱된 스탯
    ):
        if key in extra:
            extra_payload[key] = extra[key]
    if extra_payload:
        result['extra_attributes'] = extra_payload
    
    return result


def _serialize_accessory(item: Dict[str, Any]) -> Dict[str, Any]:
    """악세서리 데이터를 statscalc payload 형식으로 변환"""
    result = _serialize_item(item)
    extra = item.get('extra_attributes', {})
    
    if extra.get('enrichment'):
        result['enrichment'] = extra['enrichment']
    if extra.get('tuning'):
        result['tuning'] = extra['tuning']
    
    return result


def _build_profile_cards(profiles: Optional[Any]) -> Tuple[Dict[str, str], ...]:
    if not profiles:
        return (
            {
                'label': 'No profiles yet',
                'mode': 'Standard',
                'members': '0 members',
                'last_save': 'Last save unknown',
            },
        )

    cards: List[Dict[str, str]] = []
    for profile in profiles[:3]:
        if not isinstance(profile, dict):
            continue
        label = profile.get('cute_name') or profile.get('name') or 'Profile'
        mode = (profile.get('game_mode') or 'Standard').replace('_', ' ').title()
        members = profile.get('member_count')
        if not isinstance(members, int):
            members = 0
        last_save = _format_relative_timestamp(profile.get('last_save'))
        cards.append(
            {
                'label': label,
                'mode': mode,
                'members': f"{members} member{'s' if members != 1 else ''}",
                'last_save': f'Last save {last_save}',
            }
        )
    return tuple(cards) or (
        {
            'label': 'No profiles yet',
            'mode': 'Standard',
            'members': '0 members',
            'last_save': 'Last save unknown',
        },
    )

def _decode_preview_payload(encoded: Optional[str]) -> Optional[Dict[str, Any]]:
    if not encoded:
        return None
    try:
        padding = '=' * (-len(encoded) % 4)
        raw = base64.urlsafe_b64decode(f'{encoded}{padding}'.encode('utf-8'))
        data = json.loads(raw.decode('utf-8'))
        if isinstance(data, dict):
            return data
    except (ValueError, json.JSONDecodeError) as exc:
        LOGGER.debug('Failed to decode preview payload: %s', exc)
    return None


def _draw_preview_background(width: int, height: int) -> Image.Image:
    base = Image.new('RGBA', (width, height), (7, 10, 24, 255))
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, height * 0.55, width, height), fill=(5, 8, 18, 235))
    draw.ellipse(
        (-width * 0.45, -height * 0.65, width * 0.55, height * 0.35),
        fill=(62, 90, 220, 120),
    )
    draw.ellipse(
        (width * 0.15, -height * 0.3, width * 1.2, height * 0.9),
        fill=(28, 113, 241, 95),
    )
    draw.ellipse(
        (-width * 0.15, height * 0.35, width * 0.65, height * 1.3),
        fill=(22, 170, 190, 70),
    )
    return Image.alpha_composite(base, overlay)


def _render_player_preview_image(payload: Dict[str, Any], fallback_name: str) -> Image.Image:
    width, height = 1200, 630
    canvas = _draw_preview_background(width, height)
    draw = ImageDraw.Draw(canvas)

    label_font = _load_font(52, 'regular')
    name_font = _load_font(160, 'semibold')
    stat_font = _load_font(76, 'semibold')
    info_font = _load_font(56, 'regular')

    player_name = (payload.get('name') or fallback_name).strip() or fallback_name
    profile_list = payload.get('profiles') or []
    profile_count = len(profile_list)

    draw.text((80, 40), 'AltSky', font=label_font, fill=(194, 205, 230))
    draw.text((80, 100), player_name, font=name_font, fill=(247, 249, 255))
    draw.text(
        (80, 280),
        f"{profile_count} profile{'s' if profile_count != 1 else ''}",
        font=stat_font,
        fill=(226, 232, 255),
    )

    footer = f'altsky.info/u/{fallback_name}'
    draw.text((80, height - 80), footer, font=info_font, fill=(168, 178, 209))

    if payload.get('error'):
        error_message = payload.get('message') or payload.get('error')
        draw.text((80, height - 80), f"⚠ {error_message}", font=info_font, fill=(248, 130, 130))

    return canvas.convert('RGB')



def _render_site_preview_image() -> Image.Image:
    width, height = 1200, 630
    canvas = _draw_preview_background(width, height)
    draw = ImageDraw.Draw(canvas)

    hero_font = _load_font(200, 'semibold')

    # Only render the brand name, no other text or panels
    draw.text((80, 180), 'AltSky', font=hero_font, fill=(247, 249, 255))

    return canvas.convert('RGB')


def _render_site_preview_image_v3() -> Image.Image:
    width, height = 1200, 630

    # Layer 1: base and soft glows for depth
    base = Image.new('RGBA', (width, height), (8, 10, 22, 255))
    glow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((-260, -200, 520, 460), fill=(102, 142, 255, 150))
    glow_draw.ellipse((380, -140, 1100, 460), fill=(72, 214, 197, 120))
    glow_draw.ellipse((80, 260, 1040, 980), fill=(255, 198, 109, 75))
    canvas = Image.alpha_composite(base, glow)

    # Layer 2: subtle ribbons to break flatness
    stripes = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    stripes_draw = ImageDraw.Draw(stripes)
    for index in range(8):
        y = 400 + index * 28
        opacity = max(0, 110 - index * 12)
        stripes_draw.rectangle((-80, y, width + 120, y + 22), fill=(6, 12, 28, opacity))
    canvas = Image.alpha_composite(canvas, stripes)

    # Layer 3: glass card on the right highlighting features
    card_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_layer)
    card_draw.rounded_rectangle((760, 120, 1120, 480), fill=(255, 255, 255, 18), outline=(255, 255, 255, 45), width=2, radius=28)
    card_draw.rectangle((780, 180, 1100, 182), fill=(255, 255, 255, 30))

    spotlight_title = _load_font(38, 'semibold')
    spotlight_body = _load_font(32, 'regular')
    card_draw.text((800, 200), 'Spotlight', font=spotlight_title, fill=(228, 236, 255))
    card_draw.text(
        (800, 246),
        'Clean OG previews\nFast profile loads\nNeat gear cards',
        font=spotlight_body,
        fill=(205, 213, 231),
    )

    chips = ('Profiles', 'Gear', 'Skills')
    chip_font = _load_font(30, 'semibold')
    chip_x = 800
    chip_y = 360
    for label in chips:
        text_w, text_h = card_draw.textsize(label, font=chip_font)
        padding = 16
        rect = (chip_x, chip_y, chip_x + text_w + padding * 2, chip_y + text_h + 12)
        card_draw.rounded_rectangle(rect, radius=14, fill=(255, 255, 255, 32), outline=(255, 255, 255, 60), width=1)
        card_draw.text((chip_x + padding, chip_y + 6), label, font=chip_font, fill=(232, 239, 255))
        chip_x += text_w + padding * 2 + 14

    canvas = Image.alpha_composite(canvas, card_layer)

    # Layer 4: hero lockup
    draw = ImageDraw.Draw(canvas)
    hero_font = _load_font(206, 'semibold')
    sub_font = _load_font(52, 'regular')
    body_font = _load_font(40, 'regular')
    accent_font = _load_font(32, 'semibold')

    draw.line(((82, 128), (220, 128)), fill=(132, 198, 255), width=4)
    draw.text((82, 140), 'Preview refresh', font=accent_font, fill=(183, 212, 255))
    draw.text((80, 176), 'AltSky', font=hero_font, fill=(247, 249, 255))
    draw.text((86, 340), 'Hypixel SkyBlock profiles,\ncalmer previews, faster lookups.', font=sub_font, fill=(222, 230, 247))
    draw.text((88, 470), 'Fresh OG image · Cache-safe URL · Mobile friendly framing', font=body_font, fill=(199, 210, 232))
    draw.text((88, 520), 'altsky.info', font=body_font, fill=(170, 199, 255))

    return canvas.convert('RGB')


def _build_png_response(image: Image.Image) -> HttpResponse:
    buffer = BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response['Pragma'] = 'no-cache'
    return response


@api_view(['GET'])
def player_preview_image(request: Request, name: str) -> HttpResponse:
    provided = _decode_preview_payload(request.GET.get('payload')) if request else None
    if provided:
        provided.setdefault('name', name)
        payload = provided  # type: ignore[assignment]
    else:
        payload, _ = _get_player_lookup_result(name)

    image = _render_player_preview_image(payload, name)
    return _build_png_response(image)


@api_view(['GET'])
def site_preview_image(_: Request) -> HttpResponse:
    return _build_png_response(_render_site_preview_image())


@api_view(['GET'])
def site_preview_image_v2(_: Request) -> HttpResponse:
    return _build_png_response(_render_site_preview_image())


@api_view(['GET'])
def site_preview_image_v3(_: Request) -> HttpResponse:
    return _build_png_response(_render_site_preview_image_v3())


@api_view(['GET'])
def get_armor_texture_view(request: Request, item_id: str, layer: str) -> HttpResponse:
    """
    Serves the armor texture for a given item ID and layer (1 or 2).
    """
    LOGGER.info(f"Requesting armor texture for {item_id} layer {layer}")
    layer_1_path, layer_2_path = get_armor_textures(item_id)
    
    file_path = None
    if layer == '1':
        file_path = layer_1_path
    elif layer == '2':
        file_path = layer_2_path
        
    if not file_path:
        LOGGER.warning(f"Armor texture path not found for {item_id} layer {layer}")
        return HttpResponse(status=404)
        
    if not os.path.exists(file_path):
        LOGGER.warning(f"Armor texture file missing at {file_path}")
        return HttpResponse(status=404)
        
    try:
        with open(file_path, 'rb') as f:
            return HttpResponse(f.read(), content_type="image/png")
    except Exception as e:
        LOGGER.error(f"Error serving armor texture {file_path}: {e}")
        return HttpResponse(status=500)


@api_view(["GET"])
def get_vanilla_armor_texture_view(request: Request, name: str, layer: str) -> Response:
    """
    Returns a tinted vanilla armor texture.
    Query params:
    - color: Hex color code (e.g. c83200)
    """
    color_hex = request.query_params.get("color")
    print(f"DEBUG: Vanilla armor request: name={name}, layer={layer}, color={color_hex}", flush=True)

    # Fix for leather armor sometimes missing color (appearing gray)
    if not color_hex or color_hex.lower() in ("undefined", "null", "none"):
        if name == "leather":
            color_hex = "A06540"
        else:
            color_hex = None
    
    # Base URL for 1.8.9 assets
    base_url = "https://cdn.jsdelivr.net/gh/InventivetalentDev/minecraft-assets@1.8.9/assets/minecraft/textures/models/armor"
    filename = f"{name}_layer_{layer}.png"
    url = f"{base_url}/{filename}"
    
    # Cache key
    cache_key = f"vanilla_armor_{name}_{layer}_{color_hex or 'none'}"
    cached_data = cache.get(cache_key)
    if cached_data:
        print(f"DEBUG: Serving cached vanilla armor: {cache_key}", flush=True)
        return HttpResponse(cached_data, content_type="image/png")

    try:
        # Fetch texture
        print(f"DEBUG: Fetching upstream texture: {url}", flush=True)
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            print(f"DEBUG: Upstream texture not found: {url} (status {res.status_code})", flush=True)
            return Response({"error": "Texture not found upstream"}, status=404)
            
        img_data = BytesIO(res.content)
        img = Image.open(img_data).convert("RGBA")
        
        # Apply tint if color provided
        if color_hex:
            try:
                print(f"DEBUG: Applying tint: {color_hex}", flush=True)
                # Parse hex color
                color_hex = color_hex.lstrip("#")
                r = int(color_hex[0:2], 16)
                g = int(color_hex[2:4], 16)
                b = int(color_hex[4:6], 16)
                
                # Split channels
                r_chan, g_chan, b_chan, a_chan = img.split()
                
                # Multiply each channel
                r_chan = r_chan.point(lambda i: (i * r) // 255)
                g_chan = g_chan.point(lambda i: (i * g) // 255)
                b_chan = b_chan.point(lambda i: (i * b) // 255)
                
                # Recombine
                img = Image.merge("RGBA", (r_chan, g_chan, b_chan, a_chan))
                print("DEBUG: Tint applied successfully", flush=True)
                
            except Exception as e:
                print(f"DEBUG: Failed to tint image: {e}", flush=True)
                # Continue with original image if tint fails
        else:
            print("DEBUG: No color provided, skipping tint", flush=True)
        
        # Save to buffer
        output = BytesIO()
        img.save(output, format="PNG")
        data = output.getvalue()
        
        # Cache for 1 hour
        cache.set(cache_key, data, 3600)
        
        return HttpResponse(data, content_type="image/png")
        
    except Exception as e:
        print(f"DEBUG: Error serving vanilla armor: {e}", flush=True)
        return Response({"error": str(e)}, status=500)


@api_view(["POST", "GET"])
def get_item_textures_batch(request: Request) -> Response:
    """
    Get textures for multiple items at once.
    
    POST body or GET params:
    - item_ids: List of item IDs (comma-separated for GET)
    - pack: Texture pack ('vanilla' or 'furfsky'), default 'furfsky'
    
    Returns:
    {
        "textures": {
            "ITEM_ID": "texture_url",
            ...
        }
    }
    """
    if request.method == "POST":
        item_ids = request.data.get("item_ids", [])
        pack = request.data.get("pack", "furfsky")
    else:
        item_ids_raw = request.query_params.get("item_ids", "")
        item_ids = [i.strip() for i in item_ids_raw.split(",") if i.strip()]
        pack = request.query_params.get("pack", "furfsky")
    
    if not item_ids:
        return Response({"textures": {}})
    item_ids = item_ids[:500]
    
    textures: Dict[str, Optional[str]] = {}
    for item_id in item_ids:
        texture_url = resolve_item_icon_for_pack(item_id, None, None, pack=pack)
        textures[item_id] = texture_url
    
    return Response({"textures": textures})


# ===== Bazaar Flip Recommendations =====
HYPIXEL_BAZAAR_URL = 'https://api.hypixel.net/v2/skyblock/bazaar'
BAZAAR_CACHE_SECONDS = _read_int_env('BAZAAR_CACHE_SECONDS', 60)


def _fetch_bazaar_data(*, force_refresh: bool = False) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Fetch bazaar data from Hypixel API with caching."""
    cache_key = 'hypixel_bazaar_data'
    if not force_refresh and BAZAAR_CACHE_SECONDS > 0:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached, None

    try:
        response = _SESSION.get(HYPIXEL_BAZAAR_URL, timeout=12)
    except requests.RequestException as exc:
        return None, {'error': 'bazaar_request_failed', 'detail': str(exc), 'status': 502}

    if response.status_code != 200:
        return None, {'error': 'bazaar_fetch_failed', 'status': response.status_code}

    try:
        data = response.json()
    except ValueError:
        return None, {'error': 'bazaar_invalid_json', 'status': 502}

    if not data.get('success'):
        return None, {'error': 'bazaar_api_error', 'status': 502}

    products = data.get('products', {})
    if BAZAAR_CACHE_SECONDS > 0:
        cache.set(cache_key, products, timeout=BAZAAR_CACHE_SECONDS)

    return products, None


def _calculate_flip_recommendations(products: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
    """
    Calculate flip recommendations based on bazaar data.
    This is a placeholder - the actual calculation logic will be provided by the user.
    
    Returns a list of recommended items with flip data.
    """
    recommendations = []
    
    # Hypixel quick_status semantics:
    # - buyPrice  : price to BUY instantly (lowest sell offer / ask)
    # - sellPrice : price to SELL instantly (highest buy order / bid)
    # For flip approximation (buy order -> sell offer):
    #   revenue ~= buyPrice * (1 - tau)
    #   cost    ~= sellPrice
    # This function assumes tau=0.0125 unless overwritten by caller.
    tau = 0.0125

    for product_id, product_data in products.items():
        quick_status = product_data.get('quick_status', {})
        
        buy_price = quick_status.get('buyPrice', 0)   # instant buy (ask)
        sell_price = quick_status.get('sellPrice', 0) # instant sell (bid)
        buy_volume = quick_status.get('buyVolume', 0)
        sell_volume = quick_status.get('sellVolume', 0)
        buy_orders = quick_status.get('buyOrders', 0)
        sell_orders = quick_status.get('sellOrders', 0)
        
        # Skip items with no data
        if buy_price <= 0 or sell_price <= 0:
            continue
        
        # Flip margin: buy via buy order (≈ sellPrice), sell via sell offer (≈ buyPrice)
        margin = buy_price * (1.0 - tau) - sell_price
        margin_percent = (margin / sell_price * 100) if sell_price > 0 else 0
        
        # Calculate potential profit (simplified)
        # This is where the user's custom logic will go
        potential_profit = margin * min(buy_volume, sell_volume) * 0.01  # Placeholder
        
        recommendations.append({
            'product_id': product_id,
            'name': product_id.replace('_', ' ').title(),
            # Keep Hypixel naming in API output
            'buy_price': round(float(buy_price), 2),
            'sell_price': round(float(sell_price), 2),
            # Helpful explicit mapping for flip math
            'sell_offer_price': round(float(buy_price), 2),
            'buy_order_price': round(float(sell_price), 2),
            'tax_rate': tau,
            'margin': round(margin, 2),
            'margin_percent': round(margin_percent, 2),
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'buy_orders': buy_orders,
            'sell_orders': sell_orders,
            'potential_profit': round(potential_profit, 2),
        })
    
    # Sort by margin_percent descending (can be customized)
    recommendations.sort(key=lambda x: x['margin_percent'], reverse=True)
    
    return recommendations[:limit]


@api_view(['GET'])
@rate_limit('bazaar_flips', requests=30, window=60)
def bazaar_flips(request: Request) -> Response:
    """
    Get bazaar flip recommendations.
    
    Query params:
    - limit: Number of recommendations to return (default 20, max 100)
    - sort: Sort by 'margin', 'margin_percent', 'profit', 'volume' (default 'margin_percent')
    - refresh: Force refresh cache
    
    Returns:
    {
        "success": true,
        "recommendations": [...],
        "last_updated": "2024-01-01T00:00:00Z"
    }
    """
    force_refresh = _should_bypass_cache(request.query_params)
    limit = min(int(request.query_params.get('limit', 20)), 100)
    sort_by = request.query_params.get('sort', 'margin_percent')
    # Optional override of bazaar tax (default 1.25%)
    tau = 0.0125
    raw_tau = request.query_params.get('tax')
    if raw_tau is not None:
        try:
            tau = max(0.0, min(0.5, float(raw_tau)))
        except (TypeError, ValueError):
            tau = 0.0125
    
    products, error = _fetch_bazaar_data(force_refresh=force_refresh)
    if error:
        return Response(error, status=error.get('status', 500))
    
    # Inject tau into calculator via temporary attribute on request scope
    # (keeps signature stable while allowing the UI to override tax)
    # NOTE: if you refactor, pass tau explicitly.
    recommendations = _calculate_flip_recommendations(products, limit=limit)
    # Patch tax_rate/margins if overridden
    if tau != 0.0125:
        for rec in recommendations:
            try:
                buy_price = float(rec.get('buy_price') or 0.0)
                sell_price = float(rec.get('sell_price') or 0.0)
                margin = buy_price * (1.0 - tau) - sell_price
                rec['tax_rate'] = tau
                rec['margin'] = round(margin, 2)
                rec['margin_percent'] = round((margin / sell_price * 100) if sell_price > 0 else 0.0, 2)
            except Exception:
                continue
    
    # Apply sorting
    sort_keys = {
        'margin': 'margin',
        'margin_percent': 'margin_percent',
        'profit': 'potential_profit',
        'volume': 'buy_volume',
    }
    sort_key = sort_keys.get(sort_by, 'margin_percent')
    recommendations.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
    
    return Response({
        'success': True,
        'recommendations': recommendations,
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'total_products': len(products) if products else 0,
    })


@api_view(['GET'])
@rate_limit('bazaar_allocate', requests=30, window=60)
def bazaar_allocate(request: Request) -> Response:
    """One-shot allocator endpoint.

    Query params:
    - slots: int (S_total)
    - capital: float (W_free)
    - tax: float (tau) default 0.0125
    - top: int default 20
    - refresh: bypass bazaar cache
    - eta, phi, omega, xi, z, lambda_slot, mu, T_set: optional floats

    Returns AllocationResult JSON.
    """

    try:
        S_total = int(request.query_params.get('slots', 0))
        W_free = float(request.query_params.get('capital', 0))
    except (TypeError, ValueError):
        return Response({'error': 'invalid_params', 'detail': 'slots/capital must be numeric'}, status=400)

    if S_total <= 0 or W_free <= 0:
        return Response({'error': 'invalid_params', 'detail': 'slots and capital are required (>0)'}, status=400)

    def _get_float(name: str, default: float) -> float:
        raw = request.query_params.get(name)
        if raw is None:
            return default
        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    tau = _get_float('tax', 0.0125)
    top_n = int(request.query_params.get('top', 20) or 20)

    cfg = AllocatorConfig(S_total=S_total, W_free=W_free, top_n=max(1, min(100, top_n)))
    gp = default_global_params(
        tau=tau,
        eta=_get_float('eta', 0.8),
        phi=_get_float('phi', 0.5),
        omega=_get_float('omega', 0.45),
        xi=_get_float('xi', 0.15),
        z=_get_float('z', 2.0),
        lambda_slot=_get_float('lambda_slot', 0.0),
        mu=_get_float('mu', 0.0),
        T_set=_get_float('T_set', 1.5),
    )

    force_refresh = _should_bypass_cache(request.query_params)
    products, error = _fetch_bazaar_data(force_refresh=force_refresh)
    if error:
        return Response(error, status=error.get('status', 500))

    markets = to_market_snapshot(products or {})

    # Optional caps via JSON string in query (?caps={"ITEM":123})
    caps: Dict[str, int] = {}
    raw_caps = request.query_params.get('caps')
    if raw_caps:
        try:
            caps = load_caps_from_dict(json.loads(raw_caps))
        except Exception:
            caps = {}

    # Persisted calibrator state (optional). If not writable, still works.
    state_path = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'bazaar_allocator_state.json')
    state_path = os.path.abspath(state_path)
    calibrator = Calibrator(state_path)

    params_by_item: Dict[str, Any] = {}
    for m in markets:
        params_by_item[m.item_id] = calibrator.get_item_params(m, cfg)

    result = allocate(markets, cfg, gp, params_by_item, caps=caps)
    try:
        calibrator.save()
    except Exception:
        pass

    return Response(result.to_jsonable())
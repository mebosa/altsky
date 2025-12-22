import base64
import json
import logging
import mimetypes
import os
from datetime import datetime, timezone
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
from .domain.item_textures import load_furfsky_texture
from .domain.profile_summary import count_coop_members, summarize_profile
from .domain.armor_textures import get_armor_textures
from . import statscalc_client

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
    return HttpResponse(payload, content_type=content_type or "application/octet-stream")


VANILLA_TEXTURE_CACHE_DIR = os.path.join(os.path.dirname(__file__), "domain", "texture_cache")
VANILLA_ASSET_BASE = (
    "https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.20.1"
    "/assets/minecraft/textures"
)


def serve_vanilla_texture(request, path):
    """
    Proxy vanilla Minecraft textures from GitHub, caching locally to avoid CORS issues.
    """
    # Ensure cache directory exists
    os.makedirs(VANILLA_TEXTURE_CACHE_DIR, exist_ok=True)
    
    # Generate cache filename
    safe_filename = path.replace("/", "_").replace("\\", "_")
    cache_path = os.path.join(VANILLA_TEXTURE_CACHE_DIR, f"vanilla_{safe_filename}")
    
    # Check if cached
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                payload = f.read()
            content_type, _ = mimetypes.guess_type(path)
            response = HttpResponse(payload, content_type=content_type or "image/png")
            response["Cache-Control"] = "public, max-age=86400"
            return response
        except OSError:
            pass
    
    # Fetch from GitHub
    url = f"{VANILLA_ASSET_BASE}/{path}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            LOGGER.debug("Vanilla texture not found: %s (status=%s)", path, response.status_code)
            return HttpResponse(status=404)
        
        payload = response.content
        
        # Cache the response
        try:
            with open(cache_path, "wb") as f:
                f.write(payload)
        except OSError as exc:
            LOGGER.warning("Failed to cache vanilla texture %s: %s", path, exc)
        
        content_type, _ = mimetypes.guess_type(path)
        http_response = HttpResponse(payload, content_type=content_type or "image/png")
        http_response["Cache-Control"] = "public, max-age=86400"
        return http_response
        
    except requests.RequestException as exc:
        LOGGER.warning("Failed to fetch vanilla texture %s: %s", path, exc)
        return HttpResponse(status=404)


HYPIXEL_PROFILES_URL = 'https://api.hypixel.net/v2/skyblock/profiles'
HYPIXEL_PLAYER_URL = 'https://api.hypixel.net/v2/player'
HYPIXEL_PROFILES_CACHE_SECONDS = _read_int_env('HYPIXEL_PROFILES_CACHE_SECONDS', 20)
HYPIXEL_PLAYER_CACHE_SECONDS = _read_int_env('HYPIXEL_PLAYER_CACHE_SECONDS', 120)


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
        response = requests.get(
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
                result = requests.get(
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

    summary = summarize_profile(normalized_member_uuid, target, achievements=achievements)
    if not summary:
        return Response({'error': 'member_not_in_profile'}, status=404)

    computed_stats = None
    # 원본 member 데이터를 함께 전달
    member_data = target.get('members', {}).get(normalized_member_uuid)
    
    # skip_stats 파라미터 확인
    skip_stats = _is_truthy(request.query_params.get('skip_stats'))
    
    stat_breakdown = None
    if not skip_stats:
        stats_payload = _build_statscalc_payload(summary, normalized_member_uuid, profile_id, member_data)
        if stats_payload:
            calc_result = statscalc_client.calculate_stats(stats_payload)
            if calc_result:
                computed_stats = calc_result.get('stats')
                stat_breakdown = calc_result.get('breakdown')

    response_body = {
        'ok': True,
        'last_updated': body.get('last_updated') or body.get('lastUpdated'),
        **summary,
    }
    if computed_stats:
        response_body['computed_stats'] = computed_stats
    if stat_breakdown:
        response_body['stat_breakdown'] = stat_breakdown

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


def _build_statscalc_payload(
    summary: Dict[str, Any], 
    uuid: str, 
    profile_id: str,
    member_data: Optional[Dict[str, Any]] = None
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
            extract_pets_from_profile,
            extract_hotm_from_profile,
            extract_dungeons_from_profile,
        )
        
        # 장비 (방어구)
        equipment_data = extract_equipment_from_profile(member_data)
        if any(equipment_data.values()):
            equipment_payload = {}
            for slot, item in equipment_data.items():
                if item:
                    equipment_payload[slot] = _serialize_item(item)
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

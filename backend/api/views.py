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
from .domain.profile_summary import is_active_member, summarize_profile

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


def _get_player_lookup_result(name: str) -> Tuple[Dict[str, Any], int]:
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

        body, error = _fetch_hypixel_profiles(uuid)
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

            active_members = sum(
                1 for data in members.values() if is_active_member(data, now_ms=now_ms)
            )
            # Count only active coop members to avoid inflating with historical entries
            member_count = active_members

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
def player_lookup(_: Request, name: str) -> Response:
    payload, status_code = _get_player_lookup_result(name)
    return Response(payload, status=status_code)


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

    hero_font = _load_font(170, 'semibold')
    sub_font = _load_font(60, 'semibold')
    chip_font = _load_font(46, 'regular')
    panel_title_font = _load_font(50, 'semibold')
    panel_body_font = _load_font(40, 'regular')

    draw.text((80, 80), 'AltSky', font=hero_font, fill=(247, 249, 255))
    draw.text(
        (80, 230),
        'Hypixel SkyBlock lookup',
        font=sub_font,
        fill=(218, 224, 240),
    )

    chip_text = 'Player preview · Wardrobe · Accessories'
    bbox = draw.textbbox((0, 0), chip_text, font=chip_font)
    draw.rounded_rectangle(
        (80, 330, 80 + bbox[2] + 40, 330 + bbox[3] + 28),
        radius=28,
        fill=(32, 46, 86, 235),
        outline=(120, 135, 255, 160),
    )
    draw.text((100, 340), chip_text, font=chip_font, fill=(224, 231, 255))

    panel_left = width * 0.55
    panel_top = 120
    panel_right = width - 80
    panel_bottom = height - 80
    draw.rounded_rectangle(
        (panel_left, panel_top, panel_right, panel_bottom),
        radius=34,
        fill=(15, 20, 42, 235),
        outline=(90, 104, 196, 120),
    )

    feature_cards = [
        {
            'title': 'Player previews',
            'lines': [
                'Share /u/<name> links instantly',
                'Shows live cache & UUID',
            ],
        },
        {
            'title': 'Wardrobe snapshot',
            'lines': [
                'Server-side FurfSky textures',
                'Equipped armor highlighted',
            ],
        },
        {
            'title': 'Accessories & tuning',
            'lines': [
                'Magical power counted cleanly',
                'Readable tuning breakdown',
            ],
        },
    ]

    card_height = (panel_bottom - panel_top - 60) / len(feature_cards)
    for idx, feature in enumerate(feature_cards):
        top = panel_top + 20 + idx * (card_height + 20)
        draw.rounded_rectangle(
            (panel_left + 26, top, panel_right - 26, top + card_height),
            radius=26,
            fill=(23, 28, 62, 255),
            outline=(126, 140, 228, 90),
        )
        draw.text((panel_left + 50, top + 22), feature['title'], font=panel_title_font, fill=(247, 249, 255))
        for line_idx, line in enumerate(feature['lines']):
            draw.text(
                (panel_left + 50, top + 80 + line_idx * 36),
                f'• {line}',
                font=panel_body_font,
                fill=(196, 205, 230),
            )

    draw.text(
        (80, height - 70),
        'altsky.info · Calm Hypixel SkyBlock lookup',
        font=panel_body_font,
        fill=(176, 186, 214),
    )

    return canvas.convert('RGB')



@api_view(['GET'])
def player_preview_image(request: Request, name: str) -> HttpResponse:
    provided = _decode_preview_payload(request.GET.get('payload')) if request else None
    if provided:
        provided.setdefault('name', name)
        payload = provided  # type: ignore[assignment]
    else:
        payload, _ = _get_player_lookup_result(name)

    image = _render_player_preview_image(payload, name)
    buffer = BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response['Pragma'] = 'no-cache'
    return response


@api_view(['GET'])
def site_preview_image(_: Request) -> HttpResponse:
    image = _render_site_preview_image()
    buffer = BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response['Pragma'] = 'no-cache'
    return response


@api_view(['GET'])
def site_preview_image_v2(_: Request) -> HttpResponse:
    image = _render_site_preview_image()
    buffer = BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response['Pragma'] = 'no-cache'
    return response

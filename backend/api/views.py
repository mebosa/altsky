from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
import os, re, requests

@api_view(["GET"])
def health(_):
    return Response({"ok": True})

@api_view(["GET"])
def player_lookup(_, name: str):
    key = f"uuid:{name.lower()}"
    uuid = cache.get(key)
    if not uuid:
        r = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{name}", timeout=5)
        if r.status_code == 204:
            return Response({"error": "not found"}, status=404)
        data = r.json()
        uuid = data.get("id")
        cache.set(key, uuid, 3600)
    return Response({"name": name, "uuid": uuid})

_UUID_RE = re.compile(r"^[0-9a-fA-F-]{32,36}$")

def _norm_uuid(u: str) -> str:
    return u.replace("-", "").lower()

@api_view(["GET"])
def profile(_, uuid: str):
    # validate & normalize
    if not _UUID_RE.match(uuid or ""):
        return Response({"error": "bad uuid"}, status=400)
    uid = _norm_uuid(uuid)

    # cache first
    ckey = f"hypixel:sbprofile:{uid}"
    cached = cache.get(ckey)
    if cached:
        return Response(cached)

    key = os.getenv("HYPIXEL_API_KEY")
    if not key:
        return Response({"error": "no hypixel api key on server"}, status=500)

    url = f"https://api.hypixel.net/v2/skyblock/profiles?uuid={uid}"
    headers = {"API-Key": key}
    r = requests.get(url, headers=headers, timeout=8)

    if r.status_code != 200:
        return Response({"error": "hypixel error", "status": r.status_code}, status=502)

    raw = r.json()
    # 얇게 요약해서 내려주기(필요시 프런트에서 raw 사용)
    profiles = raw.get("profiles") or []
    summary = {
        "uuid": uid,
        "profile_count": len(profiles),
        "profiles": [
            {
                "profile_id": p.get("profile_id"),
                "cute_name": p.get("cute_name"),
                "members_keys": list((p.get("members") or {}).keys())[:3],  # 일부만
                "last_save": max([(m.get("last_save") or 0) for m in (p.get("members") or {}).values()] or [0]),
            }
            for p in profiles
        ],
        "raw": raw  # 초기엔 디버깅 위해 함께 내려줌(나중에 제거 가능)
    }

    cache.set(ckey, summary, 300)  # 5분 캐시
    return Response(summary)

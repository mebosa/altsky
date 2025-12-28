from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..networth import HYPIXEL_BAZAAR_URL
from ...http_client import session

from .types import ItemMarket


def fetch_bazaar_products(timeout: float = 12.0) -> Dict[str, Any]:
    resp = session.get(HYPIXEL_BAZAAR_URL, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json() or {}
    if not payload.get("success"):
        raise RuntimeError("Hypixel bazaar API returned success=false")
    products = payload.get("products")
    if not isinstance(products, dict):
        return {}
    return products


def to_market_snapshot(products: Dict[str, Any]) -> List[ItemMarket]:
    out: List[ItemMarket] = []
    for item_id, p in products.items():
        if not isinstance(p, dict):
            continue
        quick = p.get("quick_status")
        if not isinstance(quick, dict):
            continue
        try:
            # Hypixel naming:
            # - buyPrice: price to buy instantly (lowest sell offer)  -> p_s (sell offer price)
            # - sellPrice: price to sell instantly (highest buy order) -> p_b (buy order price)
            # For flip modeling we treat p_b as acquisition cost via buy order, p_s as revenue via sell offer.
            buy_price = float(quick.get("sellPrice") or 0.0)
            sell_price = float(quick.get("buyPrice") or 0.0)

            # Volumes: approximate fill-rate symmetry by swapping sides
            buy_volume = float(quick.get("sellVolume") or 0.0)
            sell_volume = float(quick.get("buyVolume") or 0.0)
        except (TypeError, ValueError):
            continue
        if buy_price <= 0 or sell_price <= 0:
            continue
        out.append(
            ItemMarket(
                item_id=str(item_id),
                buy_price=buy_price,
                sell_price=sell_price,
                buy_volume=buy_volume,
                sell_volume=sell_volume,
            )
        )
    return out


def load_caps_from_dict(raw: Optional[Dict[str, Any]]) -> Dict[str, int]:
    if not raw or not isinstance(raw, dict):
        return {}
    caps: Dict[str, int] = {}
    for k, v in raw.items():
        try:
            caps[str(k)] = max(0, int(v))
        except (TypeError, ValueError):
            continue
    return caps

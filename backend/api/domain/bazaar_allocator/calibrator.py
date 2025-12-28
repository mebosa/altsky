from __future__ import annotations

import json
import math
import os
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .types import AllocatorConfig, GlobalParams, ItemMarket, ItemParams


def default_global_params(
    *,
    tau: float,
    eta: float = 0.8,
    phi: float = 0.5,
    omega: float = 0.45,
    xi: float = 0.15,
    z: float = 2.0,
    lambda_slot: float = 0.0,
    mu: float = 0.0,
    T_set: float = 1.5,
) -> GlobalParams:
    return GlobalParams(
        tau=tau,
        eta=eta,
        phi=phi,
        omega=omega,
        xi=xi,
        z=z,
        lambda_slot=lambda_slot,
        mu=mu,
        T_set=T_set,
    )


def default_item_params(m: ItemMarket, cfg: AllocatorConfig) -> ItemParams:
    # v_*: interpret buy/sell_volume as "volume per cfg.volume_window_seconds".
    v_b = max(1e-9, m.buy_volume / max(1.0, cfg.volume_window_seconds))
    v_s = max(1e-9, m.sell_volume / max(1.0, cfg.volume_window_seconds))

    # F_*: starting friction (queue depth) – unknown; start small.
    F_b = 0.0
    F_s = 0.0

    # k_*: probability of staying competitive without relist; start optimistic.
    k_b = 0.92
    k_s = 0.92

    # T_rel_*: seconds per relist action (human/bot); start with a few seconds.
    T_rel_b = 3.0
    T_rel_s = 3.0

    # sigma: price volatility proxy.
    # Assume pct volatility over 15m window if no history.
    window = 15.0 * 60.0
    pct = 0.02
    sigma = (pct * m.sell_price) / math.sqrt(window)

    return ItemParams(
        v_b=v_b,
        F_b=F_b,
        v_s=v_s,
        F_s=F_s,
        k_b=k_b,
        k_s=k_s,
        T_rel_b=T_rel_b,
        T_rel_s=T_rel_s,
        sigma=sigma,
    )


class Calibrator:
    """Minimal v1: loads/saves per-item params; optional log-driven updates later."""

    def __init__(self, state_path: str):
        self.state_path = state_path
        self.state: Dict[str, Any] = {"items": {}, "updated_at": None}
        self.load()

    def load(self) -> None:
        if not os.path.exists(self.state_path):
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, dict):
                self.state.update(payload)
        except Exception:
            return

    def save(self) -> None:
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.state_path)

    def get_item_params(self, market: ItemMarket, cfg: AllocatorConfig) -> ItemParams:
        items = self.state.setdefault("items", {})
        raw = items.get(market.item_id)
        if isinstance(raw, dict):
            try:
                return ItemParams(
                    v_b=float(raw.get("v_b")),
                    F_b=float(raw.get("F_b")),
                    v_s=float(raw.get("v_s")),
                    F_s=float(raw.get("F_s")),
                    k_b=float(raw.get("k_b")),
                    k_s=float(raw.get("k_s")),
                    T_rel_b=float(raw.get("T_rel_b")),
                    T_rel_s=float(raw.get("T_rel_s")),
                    sigma=float(raw.get("sigma")),
                )
            except Exception:
                pass
        ip = default_item_params(market, cfg)
        items[market.item_id] = asdict(ip)
        return ip

    def update_from_observations(self, observations: Optional[list[dict[str, Any]]] = None) -> None:
        # Stub: in v1 we don't estimate; leave hook for JSONL event updates.
        _ = observations
        return

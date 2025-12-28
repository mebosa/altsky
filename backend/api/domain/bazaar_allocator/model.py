from __future__ import annotations

import math
from typing import Any, Dict, Tuple

from .types import GlobalParams, ItemMarket, ItemParams


def after_tax_margin(market: ItemMarket, gp: GlobalParams) -> float:
    # m_i = p_s(1-τ) − p_b
    # Here we map:
    # - p_s (sell offer price; revenue side) ≈ Hypixel buyPrice
    # - p_b (buy order price; cost side)    ≈ Hypixel sellPrice
    return market.buy_price * (1.0 - gp.tau) - market.sell_price


def T_fill(F: float, Q: int, v: float, slots: int, eta: float) -> float:
    # (F + Q) / (v * slots^eta)
    denom = max(1e-9, v * (max(1, slots) ** eta))
    return (max(0.0, F) + max(0, Q)) / denom


def T_relist(k: float, T_rel: float, slots: int, phi: float) -> float:
    # (1/k - 1) * T_rel / slots^phi
    k_clamped = min(max(k, 1e-6), 1.0)
    base = (1.0 / k_clamped - 1.0) * max(0.0, T_rel)
    return base / (max(1, slots) ** phi)


def risk_deduction(m: float, sigma: float, T: float, z: float) -> float:
    if m <= 0:
        return 1.0
    if T <= 0:
        return 0.0
    raw = z * (max(0.0, sigma) * math.sqrt(T)) / max(1e-9, m)
    return min(1.0, max(0.0, raw))


def compute_item_metrics(
    market: ItemMarket,
    ip: ItemParams,
    gp: GlobalParams,
    Q: int,
    l_b: int,
    l_s: int,
) -> Tuple[float, float, float, float, Dict[str, Any]]:
    """Return (E, T_i, r_i, K_bar, debug)."""
    m = after_tax_margin(market, gp)
    if m <= 0 or Q <= 0:
        return -1e18, 0.0, 1.0, 0.0, {"m": m}

    T_b = T_fill(ip.F_b, Q, ip.v_b, l_b, gp.eta)
    T_s = T_fill(ip.F_s, Q, ip.v_s, l_s, gp.eta)

    delta_b = T_relist(ip.k_b, ip.T_rel_b, l_b, gp.phi)
    delta_s = T_relist(ip.k_s, ip.T_rel_s, l_s, gp.phi)
    omega_term = gp.omega * min(T_b, T_s)

    T_i = gp.T_set + T_b + T_s - omega_term + delta_b + delta_s
    T_i = max(1e-6, T_i)

    r_i = risk_deduction(m, ip.sigma, T_i, gp.z)

    # Locked capital tracks cost side (p_b)
    K_bar = market.sell_price * Q * (T_b + gp.xi * T_s) / T_i

    E = (Q * m * (1.0 - r_i)) / T_i - gp.lambda_slot * (l_b + l_s) - gp.mu * K_bar

    debug = {
        "quality": {
            # Non-filtering diagnostics only (UI can use these to flag suspicious outliers)
            "spread": market.buy_price - market.sell_price,
            "spread_percent": (
                abs(market.buy_price - market.sell_price) / market.sell_price * 100.0
                if market.sell_price > 0
                else 0.0
            ),
            "min_volume": float(min(market.buy_volume, market.sell_volume)),
            "liquidity_score": min(1.0, max(0.0, math.log10(min(market.buy_volume, market.sell_volume) + 1.0) / 6.0)),
        },
        "prices": {
            # Hypixel semantics
            "buy_price": market.buy_price,   # buyPrice (ask)
            "sell_price": market.sell_price, # sellPrice (bid)
            # v3 mapping used
            "p_s": market.buy_price,
            "p_b": market.sell_price,
            "tau": gp.tau,
        },
        "m": m,
        "time": {
            "T_set": gp.T_set,
            "T_b": T_b,
            "T_s": T_s,
            "omega_term": omega_term,
            "delta_b": delta_b,
            "delta_s": delta_s,
            "T_i": T_i,
        },
        "risk": {
            "sigma": ip.sigma,
            "z": gp.z,
            "r_i": r_i,
        },
        "capital": {
            "K_bar": K_bar,
            "mu": gp.mu,
        },
        "slots": {
            "l_b": l_b,
            "l_s": l_s,
            "eta": gp.eta,
            "phi": gp.phi,
            "lambda_slot": gp.lambda_slot,
        },
    }

    return E, T_i, r_i, K_bar, debug

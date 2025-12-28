from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from .model import compute_item_metrics, after_tax_margin
from .types import (
    AllocationResult,
    AllocatorConfig,
    GlobalParams,
    ItemDecision,
    ItemMarket,
    ItemParams,
)


def estimate_q_cap(market: ItemMarket, cfg: AllocatorConfig, explicit_caps: Dict[str, int]) -> int:
    if market.item_id in explicit_caps:
        return max(0, int(explicit_caps[market.item_id]))

    # Conservative cap derived from recent volume.
    cap_from_flow = int(max(1.0, min(market.buy_volume, market.sell_volume) * cfg.cap_volume_fraction))
    return max(1, cap_from_flow)


def best_Q_for_slots(
    market: ItemMarket,
    ip: ItemParams,
    gp: GlobalParams,
    cfg: AllocatorConfig,
    q_cap: int,
) -> Tuple[int, float, float, float, Dict[str, Any]]:
    best: Tuple[int, float, float, float, Dict[str, Any]] = (0, -1e18, 0.0, 0.0, {})

    # Affordability cap by cost-side price (p_b ≈ Hypixel sellPrice)
    affordable = int(cfg.W_free // max(1e-9, market.sell_price))
    q_cap_eff = max(0, min(q_cap, affordable))
    if q_cap_eff <= 0:
        return best

    for frac in cfg.normalized_fracs():
        Q = max(1, int(math.floor(q_cap_eff * frac)))
        E, T_i, r_i, K_bar, debug = compute_item_metrics(market, ip, gp, Q, 1, 1)
        if E > best[1]:
            best = (Q, E, T_i, r_i, {**debug, "K_bar": K_bar})

    return best


def allocate(
    markets: List[ItemMarket],
    cfg: AllocatorConfig,
    gp: GlobalParams,
    params_by_item: Dict[str, ItemParams],
    caps: Dict[str, int] | None = None,
) -> AllocationResult:
    caps = caps or {}

    # Filter: positive after-tax margin & basic sanity.
    filtered: List[ItemMarket] = []
    for m in markets:
        m_after = after_tax_margin(m, gp)
        if m_after <= cfg.min_margin:
            continue
        filtered.append(m)

    filtered.sort(key=lambda x: x.buy_volume + x.sell_volume, reverse=True)
    filtered = filtered[: cfg.max_items_considered]

    # Step A: compute base (1,1) best Q and E for each item.
    base_candidates: List[Tuple[ItemMarket, int, float, float, float, float, Dict[str, Any]]] = []
    for m in filtered:
        ip = params_by_item[m.item_id]
        q_cap = estimate_q_cap(m, cfg, caps)
        Q, E, T_i, r_i, dbg = best_Q_for_slots(m, ip, gp, cfg, q_cap)
        if Q <= 0:
            continue
        # store K_bar in dbg
        K_bar = float(dbg.get("K_bar") or 0.0)
        base_candidates.append((m, Q, E, T_i, r_i, K_bar, dbg))

    base_candidates.sort(key=lambda t: t[2], reverse=True)

    # Select items until slot/capital constraints.
    decisions: Dict[str, ItemDecision] = {}
    slots_used = 0
    capital_used = 0.0

    for m, Q, E, T_i, r_i, K_bar, dbg in base_candidates:
        if len(decisions) >= cfg.top_n:
            break
        if E <= 0:
            break
        if slots_used + 2 > cfg.S_total:
            break
        if capital_used + K_bar > cfg.W_free:
            continue

        m_after = float(dbg.get("m") or after_tax_margin(m, gp))
        decisions[m.item_id] = ItemDecision(
            item_id=m.item_id,
            Q=Q,
            l_b=1,
            l_s=1,
            E=E,
            T_i=T_i,
            r_i=r_i,
            K_bar=K_bar,
            m=m_after,
            debug={"base": dbg, "params": params_by_item[m.item_id].to_dict()},
        )
        slots_used += 2
        capital_used += K_bar

    # Step C: greedy +1 slot with max delta-E.
    def eval_with_slots(item_id: str, l_b: int, l_s: int, Q: int) -> Tuple[float, float, float, float, Dict[str, Any]]:
        mkt = next(mm for mm in filtered if mm.item_id == item_id)
        ip = params_by_item[item_id]
        E, T_i, r_i, K_bar, dbg = compute_item_metrics(mkt, ip, gp, Q, l_b, l_s)
        dbg = {**dbg, "K_bar": K_bar}
        return E, T_i, r_i, K_bar, dbg

    while slots_used < cfg.S_total and decisions:
        best_delta = 0.0
        best_move: Tuple[str, str, Tuple[float, float, float, float, Dict[str, Any]]] | None = None

        for item_id, d in decisions.items():
            # try +1 buy slot
            Eb, Tb, rb, Kb, dbgb = eval_with_slots(item_id, d.l_b + 1, d.l_s, d.Q)
            delta_b = Eb - d.E
            # try +1 sell slot
            Es, Ts, rs, Ks, dbgs = eval_with_slots(item_id, d.l_b, d.l_s + 1, d.Q)
            delta_s = Es - d.E

            if delta_b >= delta_s:
                delta = delta_b
                choice = "buy"
                new_pack = (Eb, Tb, rb, Kb, dbgb)
            else:
                delta = delta_s
                choice = "sell"
                new_pack = (Es, Ts, rs, Ks, dbgs)

            if delta > best_delta:
                # respect capital constraint if K_bar increases
                new_K = new_pack[3]
                if capital_used - d.K_bar + new_K <= cfg.W_free:
                    best_delta = delta
                    best_move = (item_id, choice, new_pack)

        if best_move is None or best_delta <= 0:
            break

        item_id, choice, (E2, T2, r2, K2, dbg2) = best_move
        d = decisions[item_id]
        if choice == "buy":
            l_b2, l_s2 = d.l_b + 1, d.l_s
        else:
            l_b2, l_s2 = d.l_b, d.l_s + 1

        capital_used = capital_used - d.K_bar + K2
        decisions[item_id] = ItemDecision(
            item_id=item_id,
            Q=d.Q,
            l_b=l_b2,
            l_s=l_s2,
            E=E2,
            T_i=T2,
            r_i=r2,
            K_bar=K2,
            m=d.m,
            debug={**d.debug, "slot_update": dbg2},
        )
        slots_used += 1

    # Step D: greedy Q increments by deltaE/deltaK.
    def q_increment_candidates() -> List[Tuple[float, str, int, Tuple[float, float, float, float, Dict[str, Any]]]]:
        cands: List[Tuple[float, str, int, Tuple[float, float, float, float, Dict[str, Any]]]] = []
        for item_id, d in decisions.items():
            mkt = next(mm for mm in filtered if mm.item_id == item_id)
            q_cap = estimate_q_cap(mkt, cfg, caps)
            if d.Q >= q_cap:
                continue
            step = max(1, int(math.ceil(q_cap * cfg.q_step_fraction)))
            newQ = min(q_cap, d.Q + step)
            ip = params_by_item[item_id]
            E2, T2, r2, K2, dbg2 = compute_item_metrics(mkt, ip, gp, newQ, d.l_b, d.l_s)
            if E2 <= d.E:
                continue
            dE = E2 - d.E
            dK = K2 - d.K_bar
            if dK <= 1e-9:
                score = float("inf")
            else:
                score = dE / dK
            cands.append((score, item_id, newQ, (E2, T2, r2, K2, {**dbg2, "K_bar": K2})))
        cands.sort(key=lambda x: x[0], reverse=True)
        return cands

    while True:
        remaining = cfg.W_free - capital_used
        if remaining <= 1e-6:
            break
        cands = q_increment_candidates()
        if not cands:
            break
        score, item_id, newQ, (E2, T2, r2, K2, dbg2) = cands[0]
        d = decisions[item_id]
        if K2 - d.K_bar > remaining:
            break
        decisions[item_id] = ItemDecision(
            item_id=item_id,
            Q=newQ,
            l_b=d.l_b,
            l_s=d.l_s,
            E=E2,
            T_i=T2,
            r_i=r2,
            K_bar=K2,
            m=d.m,
            debug={**d.debug, "q_update": dbg2, "q_score": score},
        )
        capital_used = capital_used - d.K_bar + K2

    # Finalize
    final = list(decisions.values())
    final.sort(key=lambda d: d.E, reverse=True)

    total_E = sum(d.E for d in final)
    slots_left = max(0, cfg.S_total - slots_used)
    capital_left = max(0.0, cfg.W_free - capital_used)

    return AllocationResult(
        decisions=final,
        total_E=total_E,
        slots_used=slots_used,
        slots_left=slots_left,
        capital_used=capital_used,
        capital_left=capital_left,
        debug={
            "items_considered": len(filtered),
            "base_candidates": len(base_candidates),
        },
    )

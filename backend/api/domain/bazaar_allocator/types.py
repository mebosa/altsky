from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ItemMarket:
    item_id: str
    # Hypixel quick_status semantics (kept as-is across the codebase):
    # - buy_price  == buyPrice  (price to BUY instantly; lowest sell offer / ask)
    # - sell_price == sellPrice (price to SELL instantly; highest buy order / bid)
    # v3 model mapping is handled explicitly in model.after_tax_margin().
    buy_price: float
    sell_price: float
    buy_volume: float
    sell_volume: float


@dataclass
class ItemParams:
    v_b: float
    F_b: float
    v_s: float
    F_s: float
    k_b: float
    k_s: float
    T_rel_b: float
    T_rel_s: float
    sigma: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GlobalParams:
    tau: float
    eta: float
    phi: float
    omega: float
    xi: float
    z: float
    lambda_slot: float
    mu: float
    T_set: float


@dataclass
class ItemDecision:
    item_id: str
    Q: int
    l_b: int
    l_s: int
    E: float
    T_i: float
    r_i: float
    K_bar: float
    m: float
    debug: Dict[str, Any]


@dataclass
class AllocationResult:
    decisions: List[ItemDecision]
    total_E: float
    slots_used: int
    slots_left: int
    capital_used: float
    capital_left: float
    debug: Dict[str, Any]

    def to_jsonable(self) -> Dict[str, Any]:
        return {
            "decisions": [asdict(d) for d in self.decisions],
            "summary": {
                "total_E": self.total_E,
                "slots_used": self.slots_used,
                "slots_left": self.slots_left,
                "capital_used": self.capital_used,
                "capital_left": self.capital_left,
            },
            "debug": self.debug,
        }


@dataclass(frozen=True)
class AllocatorConfig:
    S_total: int
    W_free: float
    top_n: int = 20
    q_sweep_fracs: Optional[List[float]] = None
    min_margin: float = 0.0
    volume_window_seconds: float = 3600.0
    cap_volume_fraction: float = 0.02
    q_step_fraction: float = 0.05
    max_items_considered: int = 500

    def normalized_fracs(self) -> List[float]:
        fracs = self.q_sweep_fracs or [0.1, 0.25, 0.5, 0.75, 1.0]
        out = []
        for f in fracs:
            try:
                ff = float(f)
            except (TypeError, ValueError):
                continue
            if ff <= 0:
                continue
            out.append(min(1.0, ff))
        return out or [1.0]

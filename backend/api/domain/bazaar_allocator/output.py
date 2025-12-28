from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

from .types import AllocationResult


def write_json(result: AllocationResult, path: str) -> None:
    payload = result.to_jsonable()
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()

    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def format_table(result: AllocationResult, top_n: int = 20) -> str:
    rows = []
    rows.append(
        "{:<28} {:>6} {:>3} {:>3} {:>12} {:>10} {:>8} {:>12}".format(
            "item", "Q", "b", "s", "E/sec", "T(s)", "r", "K_bar"
        )
    )
    rows.append("-" * 92)

    for d in result.decisions[:top_n]:
        rows.append(
            "{:<28} {:>6} {:>3} {:>3} {:>12.4f} {:>10.2f} {:>8.3f} {:>12.1f}".format(
                d.item_id[:28],
                d.Q,
                d.l_b,
                d.l_s,
                d.E,
                d.T_i,
                d.r_i,
                d.K_bar,
            )
        )

    rows.append("")
    rows.append(
        "slots: {used}/{total} (left {left}) | capital: {used_c:.1f}/{total_c:.1f} (left {left_c:.1f}) | ΣE: {E:.4f}".format(
            used=result.slots_used,
            total=result.slots_used + result.slots_left,
            left=result.slots_left,
            used_c=result.capital_used,
            total_c=result.capital_used + result.capital_left,
            left_c=result.capital_left,
            E=result.total_E,
        )
    )

    return "\n".join(rows)

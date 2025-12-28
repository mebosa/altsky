from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

from django.core.management.base import BaseCommand

from ...domain.bazaar_allocator.calibrator import Calibrator, default_global_params
from ...domain.bazaar_allocator.data import fetch_bazaar_products, load_caps_from_dict, to_market_snapshot
from ...domain.bazaar_allocator.optimizer import allocate
from ...domain.bazaar_allocator.output import format_table, write_json
from ...domain.bazaar_allocator.types import AllocatorConfig


class Command(BaseCommand):
    help = "Compute SkyBlock Bazaar flip allocation using efficiency function v3 (greedy slots/capital)."

    def add_arguments(self, parser):
        parser.add_argument("--slots", type=int, required=True, help="Total available slots (S_total)")
        parser.add_argument("--capital", type=float, required=True, help="Available coins (W_free)")
        parser.add_argument("--tax", type=float, default=0.0125, help="Bazaar tax rate tau (e.g. 0.0125)")
        parser.add_argument("--top", type=int, default=20, help="Top N items to output")
        parser.add_argument("--interval", type=float, default=0.0, help="Seconds between ticks (0=once)")
        parser.add_argument(
            "--out",
            type=str,
            default=os.path.join("backend", "tmp", "bazaar_allocation.json"),
            help="Output JSON path",
        )
        parser.add_argument(
            "--caps",
            type=str,
            default="",
            help="Optional JSON file mapping item_id -> Q_cap",
        )
        parser.add_argument(
            "--state",
            type=str,
            default=os.path.join("backend", "tmp", "bazaar_allocator_state.json"),
            help="Calibrator state JSON path",
        )
        parser.add_argument("--eta", type=float, default=0.8)
        parser.add_argument("--phi", type=float, default=0.5)
        parser.add_argument("--omega", type=float, default=0.45)
        parser.add_argument("--xi", type=float, default=0.15)
        parser.add_argument("--z", type=float, default=2.0)
        parser.add_argument("--lambda_slot", type=float, default=0.0)
        parser.add_argument("--mu", type=float, default=0.0)
        parser.add_argument("--T_set", type=float, default=1.5)

    def handle(self, *args, **opts):
        S_total = int(opts["slots"])
        W_free = float(opts["capital"])
        tau = float(opts["tax"])
        top_n = int(opts["top"])
        interval = float(opts["interval"])
        out_path = str(opts["out"])
        state_path = str(opts["state"])

        caps_path = str(opts.get("caps") or "").strip()
        caps: Dict[str, int] = {}
        if caps_path:
            with open(caps_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            caps = load_caps_from_dict(raw)

        cfg = AllocatorConfig(S_total=S_total, W_free=W_free, top_n=top_n)
        gp = default_global_params(
            tau=tau,
            eta=float(opts["eta"]),
            phi=float(opts["phi"]),
            omega=float(opts["omega"]),
            xi=float(opts["xi"]),
            z=float(opts["z"]),
            lambda_slot=float(opts["lambda_slot"]),
            mu=float(opts["mu"]),
            T_set=float(opts["T_set"]),
        )

        calibrator = Calibrator(state_path)

        def tick() -> None:
            products = fetch_bazaar_products()
            markets = to_market_snapshot(products)

            params_by_item: Dict[str, Any] = {}
            for m in markets:
                params_by_item[m.item_id] = calibrator.get_item_params(m, cfg)

            result = allocate(markets, cfg, gp, params_by_item, caps=caps)

            self.stdout.write(format_table(result, top_n=top_n))
            write_json(result, out_path)
            calibrator.save()

        if interval <= 0:
            tick()
            return

        self.stdout.write(f"Running bazaar allocator every {interval:.1f}s. Ctrl+C to stop.")
        while True:
            start = time.time()
            try:
                tick()
            except KeyboardInterrupt:
                self.stdout.write("Stopped.")
                break
            except Exception as exc:
                self.stderr.write(f"Tick failed: {exc}")
            elapsed = time.time() - start
            sleep_for = max(0.0, interval - elapsed)
            time.sleep(sleep_for)

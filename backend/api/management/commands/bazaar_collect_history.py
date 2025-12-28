from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from django.core.management.base import BaseCommand

from ...domain.bazaar_allocator.data import fetch_bazaar_products
from ...models import BazaarPricePoint


class Command(BaseCommand):
    help = "Collect Hypixel Bazaar buy/sell prices into DB for history charts (persistent)."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=float, default=60.0, help="Seconds between polls (default 60)")
        parser.add_argument("--once", action="store_true", help="Collect exactly once and exit")
        parser.add_argument("--retention_days", type=int, default=30, help="Delete points older than N days")
        parser.add_argument(
            "--max_products",
            type=int,
            default=0,
            help="Optional cap for number of products to store per tick (0=no cap)",
        )

    def handle(self, *args, **opts):
        interval = float(opts["interval"])
        once = bool(opts["once"])
        retention_days = int(opts["retention_days"])
        max_products = int(opts["max_products"])

        if interval <= 0 and not once:
            interval = 60.0

        def tick() -> None:
            products = fetch_bazaar_products()
            now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

            rows: List[BazaarPricePoint] = []
            for product_id, p in products.items():
                if max_products > 0 and len(rows) >= max_products:
                    break
                if not isinstance(p, dict):
                    continue
                quick = p.get("quick_status")
                if not isinstance(quick, dict):
                    continue
                try:
                    buy_price = float(quick.get("buyPrice") or 0.0)
                    sell_price = float(quick.get("sellPrice") or 0.0)
                    buy_volume = float(quick.get("buyVolume") or 0.0)
                    sell_volume = float(quick.get("sellVolume") or 0.0)
                    buy_orders = int(quick.get("buyOrders") or 0)
                    sell_orders = int(quick.get("sellOrders") or 0)
                except (TypeError, ValueError):
                    continue

                if buy_price <= 0 or sell_price <= 0:
                    continue

                rows.append(
                    BazaarPricePoint(
                        product_id=str(product_id),
                        recorded_at=now,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        buy_volume=buy_volume,
                        sell_volume=sell_volume,
                        buy_orders=buy_orders,
                        sell_orders=sell_orders,
                    )
                )

            if rows:
                BazaarPricePoint.objects.bulk_create(rows, ignore_conflicts=True, batch_size=2000)

            if retention_days > 0:
                cutoff = now - timedelta(days=retention_days)
                BazaarPricePoint.objects.filter(recorded_at__lt=cutoff).delete()

            self.stdout.write(f"[{now.isoformat()}] stored={len(rows)}")

        if once:
            tick()
            return

        self.stdout.write(f"Collecting bazaar history every {interval:.1f}s. Ctrl+C to stop.")
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
            time.sleep(max(0.0, interval - elapsed))

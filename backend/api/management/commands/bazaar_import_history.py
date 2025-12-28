from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from django.core.management.base import BaseCommand

from ...models import BazaarPricePoint


def _parse_ts(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(second=0, microsecond=0)


class Command(BaseCommand):
    help = "Import historical bazaar prices from external sources into DB (CSV/JSON/JSONL)."

    def add_arguments(self, parser):
        parser.add_argument("--path", type=str, required=True, help="Path to input file")
        parser.add_argument(
            "--format",
            type=str,
            default="csv",
            choices=["csv", "json", "jsonl"],
            help="Input format (csv/json/jsonl)",
        )
        parser.add_argument("--batch", type=int, default=2000, help="Bulk insert batch size")

    def handle(self, *args, **opts):
        path = Path(str(opts["path"]))
        fmt = str(opts["format"]).lower()
        batch = int(opts["batch"])

        if not path.exists():
            raise FileNotFoundError(str(path))

        def iter_rows() -> Iterable[Dict[str, Any]]:
            if fmt == "csv":
                with path.open("r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        yield row
                return

            if fmt == "jsonl":
                with path.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        yield json.loads(line)
                return

            # json
            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, list):
                for row in payload:
                    if isinstance(row, dict):
                        yield row
            elif isinstance(payload, dict) and isinstance(payload.get("rows"), list):
                for row in payload["rows"]:
                    if isinstance(row, dict):
                        yield row

        inserted = 0
        buffer: List[BazaarPricePoint] = []

        for row in iter_rows():
            try:
                product_id = str(row.get("product_id") or row.get("item_id") or "").strip()
                ts_raw = str(row.get("ts") or row.get("timestamp") or row.get("recorded_at") or "").strip()
                if not product_id or not ts_raw:
                    continue

                recorded_at = _parse_ts(ts_raw)
                buy_price = float(row.get("buy_price") or row.get("buyPrice") or 0.0)
                sell_price = float(row.get("sell_price") or row.get("sellPrice") or 0.0)
                if buy_price <= 0 or sell_price <= 0:
                    continue

                buy_volume = float(row.get("buy_volume") or row.get("buyVolume") or 0.0)
                sell_volume = float(row.get("sell_volume") or row.get("sellVolume") or 0.0)
                buy_orders = int(float(row.get("buy_orders") or row.get("buyOrders") or 0))
                sell_orders = int(float(row.get("sell_orders") or row.get("sellOrders") or 0))

                buffer.append(
                    BazaarPricePoint(
                        product_id=product_id,
                        recorded_at=recorded_at,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        buy_volume=buy_volume,
                        sell_volume=sell_volume,
                        buy_orders=buy_orders,
                        sell_orders=sell_orders,
                    )
                )
            except Exception:
                continue

            if len(buffer) >= batch:
                BazaarPricePoint.objects.bulk_create(buffer, ignore_conflicts=True, batch_size=batch)
                inserted += len(buffer)
                buffer = []

        if buffer:
            BazaarPricePoint.objects.bulk_create(buffer, ignore_conflicts=True, batch_size=batch)
            inserted += len(buffer)

        self.stdout.write(f"Imported rows (attempted): {inserted}")
        self.stdout.write(
            "Expected columns: ts(or timestamp/recorded_at), product_id(or item_id), buy_price, sell_price, "
            "optional: buy_volume/sell_volume/buy_orders/sell_orders"
        )

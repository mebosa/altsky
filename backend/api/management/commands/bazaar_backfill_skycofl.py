from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, List, Optional

import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from ...models import BazaarPricePoint


BASE_URL = "https://sky.coflnet.com/api"


@dataclass(frozen=True)
class BackfillStats:
	product_id: str
	points_fetched: int
	rows_written: int
	start: Optional[datetime]
	end: Optional[datetime]


def _as_utc_minute(dt: datetime) -> datetime:
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=timezone.utc)
	else:
		dt = dt.astimezone(timezone.utc)
	return dt.replace(second=0, microsecond=0)


def _parse_ts(value: Any) -> Optional[datetime]:
	if isinstance(value, datetime):
		return _as_utc_minute(value)
	if not isinstance(value, str) or not value:
		return None
	dt = parse_datetime(value)
	if dt is None:
		return None
	return _as_utc_minute(dt)


def _extract_points(payload: Any) -> List[dict]:
	if isinstance(payload, list):
		return [p for p in payload if isinstance(p, dict)]	# type: ignore[return-value]
	if isinstance(payload, dict):
		for key in ("points", "data", "items", "result"):
			v = payload.get(key)
			if isinstance(v, list):
				return [p for p in v if isinstance(p, dict)]	# type: ignore[return-value]
		# occasionally a single point object
		return [payload]
	return []


def _fetch_json(url: str, timeout: float = 30.0) -> Any:
	resp = requests.get(
		url,
		timeout=timeout,
		headers={
			"User-Agent": "altsky (history backfill; contact: local dev)",
			"Accept": "application/json",
		},
	)
	resp.raise_for_status()
	return resp.json()


def _iter_product_ids(product_ids: List[str], all_products: bool, max_products: int) -> List[str]:
	if all_products:
		payload = _fetch_json(f"{BASE_URL}/items/bazaar/tags")
		ids = [str(x) for x in payload] if isinstance(payload, list) else []
	else:
		ids = [str(x) for x in product_ids if str(x).strip()]

	if not ids:
		raise CommandError("No product ids. Use --product_id ... or --all")
	if max_products > 0:
		ids = ids[:max_products]
	return ids


class Command(BaseCommand):
	help = "Backfill Bazaar price history from SkyCofl (sky.coflnet.com) into BazaarPricePoint."

	def add_arguments(self, parser):
		parser.add_argument(
			"--product_id",
			action="append",
			default=[],
			help="Hypixel product id (repeatable). Example: --product_id ENCHANTED_CARROT",
		)
		parser.add_argument(
			"--all",
			action="store_true",
			help="Backfill all bazaar product ids as returned by SkyCofl /api/items/bazaar/tags",
		)
		parser.add_argument(
			"--max_products",
			type=int,
			default=0,
			help="Optional cap when using --all (0 = no cap)",
		)
		parser.add_argument(
			"--mode",
			choices=["hour", "day", "week", "range"],
			default="day",
			help="History window endpoint to use (default: day).",
		)
		parser.add_argument(
			"--start",
			type=str,
			default="",
			help="ISO timestamp (UTC recommended). Only used when --mode range.",
		)
		parser.add_argument(
			"--end",
			type=str,
			default="",
			help="ISO timestamp (UTC recommended). Only used when --mode range.",
		)
		parser.add_argument(
			"--sleep",
			type=float,
			default=0.0,
			help="Optional sleep seconds between item requests (rate limit friendliness).",
		)
		parser.add_argument(
			"--batch_size",
			type=int,
			default=2000,
			help="Django bulk_create batch size (default 2000)",
		)

	def handle(self, *args, **opts):
		product_ids = list(opts.get("product_id") or [])
		all_products = bool(opts.get("all"))
		max_products = int(opts.get("max_products") or 0)
		mode = str(opts.get("mode") or "day")
		sleep_s = float(opts.get("sleep") or 0.0)
		batch_size = int(opts.get("batch_size") or 2000)

		start_raw = str(opts.get("start") or "").strip()
		end_raw = str(opts.get("end") or "").strip()

		if mode == "range" and (not start_raw or not end_raw):
			raise CommandError("--mode range requires both --start and --end")
		if mode != "range" and (start_raw or end_raw):
			raise CommandError("--start/--end are only valid with --mode range")

		ids = _iter_product_ids(product_ids, all_products, max_products)

		import time

		stats: List[BackfillStats] = []
		self.stdout.write(f"SkyCofl backfill: mode={mode}, products={len(ids)}")

		for idx, product_id in enumerate(ids, start=1):
			if mode == "range":
				url = f"{BASE_URL}/bazaar/{product_id}/history?start={start_raw}&end={end_raw}"
			else:
				url = f"{BASE_URL}/bazaar/{product_id}/history/{mode}"

			try:
				payload = _fetch_json(url)
			except Exception as exc:
				self.stderr.write(f"[{idx}/{len(ids)}] {product_id}: fetch failed: {exc}")
				if sleep_s > 0:
					time.sleep(sleep_s)
				continue

			points = _extract_points(payload)
			rows: List[BazaarPricePoint] = []
			min_ts: Optional[datetime] = None
			max_ts: Optional[datetime] = None

			for p in points:
				recorded_at = _parse_ts(p.get("timestamp") or p.get("ts") or p.get("recorded_at"))
				if recorded_at is None:
					continue
				try:
					buy_price = float(p.get("buy") or p.get("buy_price") or p.get("buyPrice") or 0.0)
					sell_price = float(p.get("sell") or p.get("sell_price") or p.get("sellPrice") or 0.0)
					buy_volume = float(p.get("buyVolume") or p.get("buy_volume") or 0.0)
					sell_volume = float(p.get("sellVolume") or p.get("sell_volume") or 0.0)
				except (TypeError, ValueError):
					continue

				if buy_price <= 0 or sell_price <= 0:
					continue

				min_ts = recorded_at if min_ts is None else min(min_ts, recorded_at)
				max_ts = recorded_at if max_ts is None else max(max_ts, recorded_at)

				rows.append(
					BazaarPricePoint(
						product_id=str(product_id),
						recorded_at=recorded_at,
						buy_price=buy_price,
						sell_price=sell_price,
						buy_volume=buy_volume,
						sell_volume=sell_volume,
						buy_orders=0,
						sell_orders=0,
					)
				)

			written = 0
			if rows:
				BazaarPricePoint.objects.bulk_create(rows, ignore_conflicts=True, batch_size=batch_size)
				written = len(rows)

			stats.append(
				BackfillStats(
					product_id=str(product_id),
					points_fetched=len(points),
					rows_written=written,
					start=min_ts,
					end=max_ts,
				)
			)

			msg_range = ""
			if min_ts and max_ts:
				msg_range = f" {min_ts.isoformat()}..{max_ts.isoformat()}"
			self.stdout.write(f"[{idx}/{len(ids)}] {product_id}: fetched={len(points)} stored={written}{msg_range}")

			if sleep_s > 0:
				time.sleep(sleep_s)

		total_written = sum(s.rows_written for s in stats)
		self.stdout.write(f"Done. products_ok={len(stats)}/{len(ids)} rows_written={total_written}")

# External Bazaar History Sources

AltSky can persist Bazaar history from now on (via DB collector) and can also ingest external history files.

## What Hypixel provides

Hypixel Bazaar API is a *current snapshot* API. It does not provide an official historical time-series endpoint.

## Recommended approach

1) Start collecting now (persistent)
- Run the collector: `python backend/manage.py bazaar_collect_history --interval 60 --retention_days 30`
- This stores one point per item per minute (deduped by `(product_id, recorded_at)`).

2) Backfill older history (external)
- Obtain a dataset from a third-party archive or your own logs.
- Import it into the same DB using the importer command.

## Import formats

### CSV
Required columns:
- `ts` (ISO 8601, e.g. `2025-12-28T02:30:00Z`)
- `product_id`
- `buy_price`
- `sell_price`

Optional:
- `buy_volume`, `sell_volume`, `buy_orders`, `sell_orders`

Command:
- `python backend/manage.py bazaar_import_history --format csv --path path/to/file.csv`

### JSONL (newline-delimited JSON)
Each line:
```json
{"ts":"2025-12-28T02:30:00Z","product_id":"ENCHANTED_CARROT","buy_price":123.4,"sell_price":120.1}
```

Command:
- `python backend/manage.py bazaar_import_history --format jsonl --path path/to/file.jsonl`

### JSON
Either:
- an array of objects `[ {...}, {...} ]`, or
- `{ "rows": [ {...}, {...} ] }`

Command:
- `python backend/manage.py bazaar_import_history --format json --path path/to/file.json`

## Notes

- Timestamps are rounded to the minute when stored.
- Duplicate points are ignored by unique constraint.
- After import/collection, the UI detail page uses `/api/bazaar/history` to render an overlay chart.

## SkyCofl (Coflnet Sky API)

SkyCofl provides public Bazaar history endpoints returning a time-series with:
- `timestamp`
- `buy` (instant buy price; ask)
- `sell` (instant sell price; bid)
- `buyVolume` / `sellVolume`

API docs:
- https://sky.coflnet.com/api

Endpoints:
- `GET https://sky.coflnet.com/api/bazaar/{ITEM_TAG}/history/hour` (20s resolution)
- `GET https://sky.coflnet.com/api/bazaar/{ITEM_TAG}/history/day` (5m resolution)
- `GET https://sky.coflnet.com/api/bazaar/{ITEM_TAG}/history/week` (2h resolution)
- `GET https://sky.coflnet.com/api/bazaar/{ITEM_TAG}/history?start=...&end=...`

This repo includes:
- A management command to backfill directly into the DB: `python backend/manage.py bazaar_backfill_skycofl --product_id ENCHANTED_CARROT --mode day`
- An API opt-in backfill flag: `GET /api/bazaar/history?product_id=...&backfill=1`

Note: if you use SkyCofl data in a public project, review their attribution/usage requirements.

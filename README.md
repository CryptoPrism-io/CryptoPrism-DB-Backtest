Backtest Repo Template

Goal
- Provide a clean, self-contained template to run vectorbt backtests directly from PostgreSQL (cp_ai / cp_backtest_h), including QA checks and maintenance helpers.

What’s Included
- src/backtest.py: Vectorbt backtest runner (strict DB-only). CLI flags for date window and table names.
- src/db.py: Minimal engine factory for Postgres using .env.
- scripts/run_backtest.py: Helper launcher (works with local venv or system Python).
- scripts/qa/check_sync_last3days.py: Verifies cp_ai vs cp_backtest_h are aligned for last 3 days.
- scripts/maintenance/enforce_unique_ohlcv_slug_ts.py: Adds UNIQUE(slug,timestamp) and removes duplicates.
- scripts/maintenance/sync_ohlcv_from_cp_ai_to_backtest.py: One-off incremental sync cp_ai -> cp_backtest_h.
- .github/workflows/backtest.yml: CI to run a rolling-window backtest and upload stats artifact.
- .env.example: Environment variable template for DB credentials.
- requirements.txt: Python dependencies (Python 3.12 recommended for vectorbt wheels).

Quick Start (Local)
1) Python 3.12 venv and install deps
   - py -3.12 -m venv .venv
   - .venv\\Scripts\\activate
   - pip install -U pip
   - pip install -r requirements.txt

2) Configure environment
   - Copy .env.example to .env and fill DB_HOST, DB_USER, DB_PASSWORD, DB_NAME (cp_ai), DB_NAME_BT (cp_backtest_h)

3) Optional QA checks
   - python scripts/qa/check_sync_last3days.py

4) Run backtest
   - python src/backtest.py --list-ranges
   - python src/backtest.py --start "2025-02-13 00:00:00" --end "2025-11-04 06:00:00"

Design Notes
- Strict DB-only: if prices or signals are missing for the chosen window, the runner exits with a clear error and prints available ranges.
- Uniqueness & Sync Safety: maintenance scripts enforce UNIQUE(slug,timestamp) and use ON CONFLICT DO NOTHING for idempotent loads.
- CI: backtest.yml sets up Python 3.12, installs requirements, runs a rolling backtest (last 30 days), and uploads the stats output.


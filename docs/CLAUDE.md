# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

### Setup
```bash
# Create and activate venv (Python 3.12 recommended for vectorbt wheels)
py -3.12 -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -U pip
pip install -r requirements.txt

# Configure environment
# Copy .env.example to .env and fill in:
# DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME (cp_ai), DB_NAME_BT (cp_backtest_h)
```

### Common Commands

**List strategies and data:**
```bash
# List all available strategies
python src/backtest.py --list-strategies

# List available data ranges in the backtest database
python src/backtest.py --list-ranges
```

**Run a backtest:**
```bash
# Backtest last 30 days with default DMV signals
python src/backtest.py

# Backtest with specific strategy (MA Crossover 8h/24h)
python src/backtest.py --strategy MA_Crossover_8_24 --days 30

# Backtest single coin with strategy
python src/backtest.py --strategy MA_Crossover_8_24 --coin bitcoin --days 30

# Backtest specific time window
python src/backtest.py --start "2025-02-13 00:00:00" --end "2025-11-04 06:00:00"

# Backtest with custom N days
python src/backtest.py --days 60

# Via helper script (auto-detects venv or system Python)
python scripts/run_backtest.py --strategy MA_Fast_12 --coin ethereum --days 30
```

**Data maintenance and validation:**
```bash
# Validate sync between cp_ai and cp_backtest_h for last 3 days
python scripts/qa/check_sync_last3days.py

# One-off: Enforce UNIQUE(slug, timestamp) and remove duplicates
python scripts/maintenance/enforce_unique_ohlcv_slug_ts.py

# One-off: Incremental sync from cp_ai to cp_backtest_h
python scripts/maintenance/sync_ohlcv_from_cp_ai_to_backtest.py
```

## Architecture Overview

### Purpose
A self-contained **vectorbt-based backtesting framework** for simulating trading strategies against historical OHLCV price data and trading signals stored in PostgreSQL. Emphasizes reproducibility, data integrity, and CI/CD automation.

### Key Design Principles

1. **Strict DB-Only**: All data sourced exclusively from PostgreSQL. If required data is missing for the selected window, the runner exits with a clear error and prints available ranges.

2. **Dual-Database Pattern**:
   - `cp_ai`: Production source with raw, live data
   - `cp_backtest_h`: Isolated backtest copy with enforced constraints
   - Separation ensures reproducibility and prevents accidental contamination

3. **Idempotent Operations**: Maintenance scripts use `ON CONFLICT DO NOTHING` and can be run repeatedly without side effects (critical for CI/CD).

4. **Constraint-First Integrity**: Database-level `UNIQUE(slug, timestamp)` enforced before backtests run. Window function deduplication before constraint creation.

5. **Vectorized Backtesting**:
   - Entry: bullish signal ≥ 3
   - Exit: bullish == 0 OR bearish ≤ -2
   - Trading costs: 0.1% fees + 0.05% slippage, cash_sharing=True (single pool across assets)
   - Thin assets filtered: only coins with ≥20 non-null price points in the window

6. **Environment-Driven Config**: All database credentials and secrets in `.env` (never hardcoded).

### Directory Structure

```
src/
├── backtest.py        # Main vectorbt backtest executor with CLI
└── db.py              # SQLAlchemy engine factory for PostgreSQL

scripts/
├── run_backtest.py    # Helper launcher (detects venv or system Python)
├── qa/
│   └── check_sync_last3days.py  # Validates cp_ai ↔ cp_backtest_h sync
└── maintenance/
    ├── enforce_unique_ohlcv_slug_ts.py  # Add UNIQUE constraint, remove dups
    └── sync_ohlcv_from_cp_ai_to_backtest.py  # Incremental sync

.github/workflows/
└── backtest.yml       # Daily 30-day rolling backtest automation

requirements.txt       # Dependencies: vectorbt, pandas, sqlalchemy, psycopg2-binary, python-dotenv
.env.example          # DB credentials template
.gitignore            # Excludes .env, venv, data/, reports/
```

### Data Flow

```
1. SOURCE: cp_ai (ohlcv_1h_250_coins, FE_DMV_ALL)
2. SYNC: sync_ohlcv_from_cp_ai_to_backtest.py → cp_backtest_h
3. MAINTAIN: enforce_unique_ohlcv_slug_ts.py → Add constraints, remove dups
4. VALIDATE: check_sync_last3days.py → QA checks
5. BACKTEST: backtest.py → Load prices + signals → vectorbt simulation → stats output
6. CI: GitHub Actions → Run daily, upload artifact
```

### Core Components

**backtest.py**:
- Parses CLI args: `--start`, `--end`, `--days`, `--db-name`, `--prices-table`, `--signals-table`, `--list-ranges`
- Loads OHLCV prices and bullish/bearish signals from database
- Filters thin assets (< 20 data points)
- Runs vectorbt portfolio simulation with fixed entry/exit rules
- Outputs performance stats (total return, sharpe ratio, max drawdown, etc.)

**db.py**:
- Factory function `engine_for(db_name)` that creates SQLAlchemy engine
- Reads DB_HOST, DB_PORT, DB_USER, DB_PASSWORD from `.env`

**run_backtest.py**:
- Helper wrapper for local execution
- Prefers `.venv/Scripts/python.exe` if present, falls back to system Python
- Delegates all args to `src/backtest.py`

**Maintenance Scripts**:
- `check_sync_last3days.py`: Compares rowcounts, coin coverage, latest timestamps between cp_ai and cp_backtest_h
- `enforce_unique_ohlcv_slug_ts.py`: Uses window functions to remove duplicates, then adds `UNIQUE(slug, timestamp)` constraint and indexes
- `sync_ohlcv_from_cp_ai_to_backtest.py`: Queries latest timestamp in cp_backtest_h, fetches incremental rows from cp_ai, inserts with `ON CONFLICT DO NOTHING`

**backtest.yml CI/CD**:
- Trigger: Daily cron at 02:15 UTC or manual workflow_dispatch
- Runs: `python -m backtest-repo.src.backtest --days 30`
- Output: `backtest_stats.txt` uploaded as artifact

### Configuration

**Environment Variables** (in `.env`):
```
DB_HOST              # PostgreSQL hostname
DB_PORT              # PostgreSQL port (default 5432)
DB_USER              # PostgreSQL username
DB_PASSWORD          # PostgreSQL password
DB_NAME              # Source database (cp_ai)
DB_NAME_BT           # Backtest database (cp_backtest_h)
BBACKTEST_DAYS       # Default backtest days (optional, default 30)
```

### Strategies Framework

A modular strategy system allows multiple trading strategies to be defined and tested independently.

**Available Strategies** (in `strategies/` folder):

*Technical Indicators*:
- `MA_Crossover_8_24`: Dual MA crossover (8h fast, 24h slow)
- `MA_Fast_12`: Price vs 12h moving average

*Sentiment + Ratio Filters (Long/Short)*:
- `SentimentLong_3_1.0_1.0`: Long on bullish + ratio filters
- `SentimentShort_3_1.0_2.0`: Short on bearish + ratio filters
- `SentimentLongShort_3_3`: ⭐ Combined long/short (best performer)

**Creating New Strategies**:
1. Create a new file in `strategies/` folder
2. Inherit from `BaseStrategy` interface
3. Implement `generate_signals(close, bullish=None, bearish=None, **kwargs)` method
4. Return 2-tuple (long-only) or 4-tuple (long/short)

**Example - Long-Only**:
```python
from strategies import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="MyStrategy",
            description="Brief description"
        )

    def generate_signals(self, close, bullish=None, bearish=None, **kwargs):
        # close: DataFrame (index=timestamp, columns=coin slugs)
        entries = ...  # Boolean DataFrame
        exits = ...    # Boolean DataFrame
        return entries, exits  # 2-tuple for long-only
```

**Example - Long/Short**:
```python
def generate_signals(self, close, bullish=None, bearish=None, **kwargs):
    ratios = kwargs.get('ratios')  # Optional: dict with 'alpha', 'beta', 'omega'

    long_entries = ...     # Boolean DataFrame
    long_exits = ...       # Boolean DataFrame
    short_entries = ...    # Boolean DataFrame
    short_exits = ...      # Boolean DataFrame
    return long_entries, long_exits, short_entries, short_exits  # 4-tuple for long/short
```

Strategies are discovered automatically and can be run via `--strategy` flag. See `LONGSHORT_STRATEGIES.md` for real examples.

### Default Entry/Exit Rules (DMV Signals)

Defined in `src/backtest.py:run_vbt()` when no custom strategy is specified:

```python
entries = bullish >= 3                          # Enter when bullish ≥ 3
exits = (bullish == 0) | (bearish <= -2)      # Exit on bullish drop or bearish drop
```

Entry/exit signals come from `FE_DMV_ALL` table (bullish/bearish columns)

### Testing and Validation

This repo has **no unit tests** (it's a template/scaffold). Validation happens via:
1. **QA Script**: `scripts/qa/check_sync_last3days.py` confirms data sync integrity
2. **Manual Backtest**: Run `python src/backtest.py --list-ranges` to verify data exists before executing a backtest
3. **CI Artifacts**: GitHub Actions uploads `backtest_stats.txt` for inspection

To add unit tests for new custom logic, create a `tests/` directory and run:
```bash
pytest tests/
```

### Important Notes

- **Python 3.12**: Recommended for reliable vectorbt wheel availability
- **Database Access**: Requires PostgreSQL connection with explicit credentials in `.env`
- **Data Consistency**: If a backtest fails due to missing data, check available ranges with `--list-ranges` and check QA script for sync drift
- **CI Secrets**: Database credentials stored in GitHub repo secrets, not in code
- **Thin Asset Filtering**: Coins with < 20 price points in the backtest window are automatically excluded

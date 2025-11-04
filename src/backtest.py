#!/usr/bin/env python3
"""
Vectorbt backtest against cp_backtest_h (strict DB-only).
Supports custom strategies from the strategies/ folder.
"""

import os
import sys
import argparse
import importlib
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from dotenv import load_dotenv

from .db import engine_for


def table_exists(con, table_name: str) -> bool:
    q = text("SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=:t LIMIT 1")
    try:
        return con.execute(q, {"t": table_name}).first() is not None
    except Exception:
        return False


def load_data(con, start, end, prices_table: str, signals_table: str, ratios_table: str = None):
    if not table_exists(con, prices_table):
        raise SystemExit(f"[ERROR] Prices table '{prices_table}' not found")
    if not table_exists(con, signals_table):
        raise SystemExit(f"[ERROR] Signals table '{signals_table}' not found")

    px = pd.read_sql(
        f"""
        SELECT timestamp, slug, close
        FROM {prices_table}
        WHERE timestamp >= %(s)s AND timestamp < %(e)s
        """,
        con,
        params={"s": start, "e": end},
        parse_dates=["timestamp"],
    )
    dmv = pd.read_sql(
        f"""
        SELECT timestamp, slug, bullish, bearish
        FROM "{signals_table}"
        WHERE timestamp >= %(s)s AND timestamp < %(e)s
        """,
        con,
        params={"s": start, "e": end},
        parse_dates=["timestamp"],
    )

    close = px.pivot(index="timestamp", columns="slug", values="close").sort_index()
    bullish = dmv.pivot(index="timestamp", columns="slug", values="bullish").reindex(close.index).fillna(0)
    bearish = dmv.pivot(index="timestamp", columns="slug", values="bearish").reindex(close.index).fillna(0)

    # Find common columns across all loaded data
    common = close.columns.intersection(bullish.columns).intersection(bearish.columns)

    # Also include ratios in intersection if loaded
    if ratios_table:
        # Note: ratios dict is created later, so just note it here for now
        pass

    close = close[common]
    bullish = bullish[common]
    bearish = bearish[common]

    # Load ratio data if requested
    ratios = None
    if ratios_table:
        if not table_exists(con, ratios_table):
            print(f"[WARNING] Ratios table '{ratios_table}' not found, skipping ratio data")
        else:
            try:
                ratios_data = pd.read_sql(
                    f"""
                    SELECT timestamp, slug, m_rat_alpha, d_rat_beta, m_rat_omega
                    FROM "{ratios_table}"
                    WHERE timestamp >= %(s)s AND timestamp < %(e)s
                    """,
                    con,
                    params={"s": start, "e": end},
                    parse_dates=["timestamp"],
                )

                # Pivot ratio columns
                ratios = {
                    'alpha': ratios_data.pivot(index="timestamp", columns="slug", values="m_rat_alpha").reindex(close.index),
                    'beta': ratios_data.pivot(index="timestamp", columns="slug", values="d_rat_beta").reindex(close.index),
                    'omega': ratios_data.pivot(index="timestamp", columns="slug", values="m_rat_omega").reindex(close.index),
                }

                # Forward-fill missing ratio values (ratios change less frequently than prices)
                for key in ratios:
                    ratios[key] = ratios[key].ffill().bfill()

            except Exception as e:
                print(f"[WARNING] Error loading ratio data: {e}")
                ratios = None

    return close, bullish, bearish, ratios


def print_ranges(con, prices_table: str, signals_table: str):
    def rng(t):
        if not table_exists(con, t):
            return f"- {t}: [MISSING]"
        q = text(f"SELECT MIN(timestamp::date) min_date, MAX(timestamp::date) max_date, COUNT(DISTINCT timestamp::date) days FROM \"{t}\"")
        try:
            df = pd.read_sql(q, con)
            if df.empty:
                return f"- {t}: [EMPTY]"
            return f"- {t}: {df['min_date'].iloc[0]} -> {df['max_date'].iloc[0]} ({df['days'].iloc[0]} days)"
        except Exception as e:
            return f"- {t}: [ERROR] {str(e)[:120]}"

    print("\n== AVAILABLE RANGES (Backtest DB) ==")
    print(rng(prices_table))
    print(rng(signals_table))


def get_available_strategies() -> dict:
    """Discover and load all available strategies from strategies/ folder."""
    strategies_dir = Path(__file__).parent.parent / "strategies"
    strategies = {}

    if not strategies_dir.exists():
        return strategies

    # Add strategies folder to sys.path for imports
    sys.path.insert(0, str(strategies_dir.parent))

    # Scan for strategy modules
    for py_file in strategies_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue

        module_name = py_file.stem
        try:
            module = importlib.import_module(f"strategies.{module_name}")

            # Find all classes in the module that aren't BaseStrategy
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and attr_name != "BaseStrategy"
                    and hasattr(attr, "generate_signals")
                ):
                    # Instantiate the class
                    try:
                        instance = attr()
                        strategy_name = instance.name
                        strategies[strategy_name] = instance
                    except Exception:
                        # Skip if can't instantiate (might need args)
                        pass
        except Exception:
            pass

    return strategies


def load_strategy(strategy_name: str) -> object:
    """Load and return a strategy instance by name."""
    strategies = get_available_strategies()
    if strategy_name in strategies:
        return strategies[strategy_name]

    # List available strategies
    if strategies:
        print(f"[ERROR] Strategy '{strategy_name}' not found.")
        print("Available strategies:")
        for name in sorted(strategies.keys()):
            print(f"  - {name}: {strategies[name].description}")
    else:
        print(f"[ERROR] Strategy '{strategy_name}' not found and no strategies available.")
    raise SystemExit(1)


def print_available_strategies():
    """Print all available strategies."""
    strategies = get_available_strategies()
    if not strategies:
        print("No strategies found in strategies/ folder")
        return

    print("\n== AVAILABLE STRATEGIES ==")
    for name in sorted(strategies.keys()):
        print(f"  {name}: {strategies[name].description}")


def run_vbt(close, bullish, bearish, strategy=None, ratios=None):
    """
    Run backtest with given strategy or default DMV signals.
    Supports both long-only and long/short strategies.

    Args:
        close: Price data (DataFrame)
        bullish: Bullish signals (DataFrame)
        bearish: Bearish signals (DataFrame)
        strategy: Strategy instance, or None to use default DMV signals
        ratios: Optional dict with 'alpha', 'beta', 'omega' DataFrames
    """
    import vectorbt as vbt

    short_entries = None
    short_exits = None

    if strategy is None:
        # Default: use DMV signals (long-only)
        entries = bullish >= 3
        exits = (bullish == 0) | (bearish <= -2)
    else:
        # Use custom strategy - pass ratios as kwargs
        strategy_kwargs = {'close': close, 'bullish': bullish, 'bearish': bearish}
        if ratios:
            strategy_kwargs['ratios'] = ratios

        signals = strategy.generate_signals(**strategy_kwargs)

        # Check if strategy returns 4-tuple (long/short) or 2-tuple (long-only)
        if isinstance(signals, tuple) and len(signals) == 4:
            entries, exits, short_entries, short_exits = signals
        else:
            entries, exits = signals
            # Keep short_entries and short_exits as None for long-only strategies

    # Build kwargs for Portfolio.from_signals
    pf_kwargs = {
        'init_cash': 100_000,
        'fees': 0.001,
        'slippage': 0.0005,
        'cash_sharing': True,
        'freq': '1h'
    }

    # Add short positions if strategy provides them
    if short_entries is not None:
        pf_kwargs['short_entries'] = short_entries
        pf_kwargs['short_exits'] = short_exits

    pf = vbt.Portfolio.from_signals(close, entries, exits, **pf_kwargs)
    return pf


def parse_args():
    p = argparse.ArgumentParser(description="Vectorbt backtest against cp_backtest_h (strict)")
    p.add_argument("--start", type=str, help="UTC start datetime, e.g. 2025-02-13 00:00:00")
    p.add_argument("--end", type=str, help="UTC end datetime, e.g. 2025-11-04 06:00:00")
    p.add_argument("--days", type=int, default=int(os.getenv("BBACKTEST_DAYS", "30")), help="If no start/end, use last N days")
    p.add_argument("--db-name", type=str, default=os.getenv("DB_NAME_BT", "cp_backtest_h"))
    p.add_argument("--prices-table", type=str, default="ohlcv_1h_250_coins")
    p.add_argument("--signals-table", type=str, default="FE_DMV_ALL")
    p.add_argument("--strategy", type=str, default=None, help="Strategy name to use (default: DMV signals)")
    p.add_argument("--coin", type=str, default=None, help="Filter to single coin slug (e.g., bitcoin)")
    p.add_argument("--list-ranges", action="store_true", help="List available data ranges")
    p.add_argument("--list-strategies", action="store_true", help="List available strategies")
    return p.parse_args()


def main():
    load_dotenv()
    args = parse_args()

    # Handle list operations
    if args.list_strategies:
        print_available_strategies()
        return

    # Load strategy if specified
    strategy = None
    if args.strategy:
        strategy = load_strategy(args.strategy)
        print(f"Strategy: {strategy}")

    # Determine window
    if args.start and args.end:
        start_dt = pd.to_datetime(args.start)
        end_dt = pd.to_datetime(args.end)
    else:
        end_dt = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        start_dt = end_dt - timedelta(days=args.days)
    start = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    print("\n== BACKTEST: SETUP ==")
    print(f"Window: {start} -> {end} (UTC)")
    print(f"DB: {args.db_name} | prices={args.prices_table} | signals={args.signals_table}")
    if args.coin:
        print(f"Asset: {args.coin}")
    if strategy:
        print(f"Strategy: {strategy.name} - {strategy.description}")
    else:
        print("Strategy: DMV Signals (default)")

    eng = engine_for(args.db_name)
    with eng.connect() as con:
        if args.list_ranges:
            print_ranges(con, args.prices_table, args.signals_table)
            return
        close, bullish, bearish, ratios = load_data(
            con, start, end, args.prices_table, args.signals_table,
            ratios_table="FE_RATIOS"
        )

    print(f"Prices shape: {close.shape}")
    print(f"Signals shape: bullish={bullish.shape}, bearish={bearish.shape}")
    if ratios:
        print(f"Ratios loaded: alpha={ratios['alpha'].shape}, beta={ratios['beta'].shape}, omega={ratios['omega'].shape}")
    if close.empty or bullish.empty or bearish.empty:
        print("[ERROR] Missing data for selected window.")
        with eng.connect() as con:
            print_ranges(con, args.prices_table, args.signals_table)
        raise SystemExit(1)

    # Filter thin assets
    nonnan_cols = close.columns[close.notna().sum() > 20]
    close = close[nonnan_cols]
    bullish = bullish.reindex(columns=nonnan_cols, fill_value=0)
    bearish = bearish.reindex(columns=nonnan_cols, fill_value=0)

    # Align ratios with available columns
    if ratios:
        # Only keep columns that exist in both close and ratios
        ratio_cols = nonnan_cols.intersection(ratios['beta'].columns)
        nonnan_cols = nonnan_cols.intersection(ratio_cols)
        close = close[nonnan_cols]
        bullish = bullish[nonnan_cols]
        bearish = bearish[nonnan_cols]
        for key in ratios:
            ratios[key] = ratios[key][nonnan_cols]

    print(f"Filtered to columns with data: {len(nonnan_cols)} assets")

    # Filter to single coin if specified
    if args.coin:
        if args.coin not in close.columns:
            print(f"[ERROR] Coin '{args.coin}' not found in data")
            print(f"Available coins: {', '.join(sorted(close.columns))}")
            raise SystemExit(1)
        close = close[[args.coin]]
        bullish = bullish[[args.coin]]
        bearish = bearish[[args.coin]]
        if ratios:
            for key in ratios:
                ratios[key] = ratios[key][[args.coin]]
        print(f"Filtered to single asset: {args.coin}")

    print("\n== BACKTEST: RUN (vectorbt) ==")
    pf = run_vbt(close, bullish, bearish, strategy=strategy, ratios=ratios)

    print("\n== BACKTEST: STATS ==")
    print(pf.stats())


if __name__ == "__main__":
    main()


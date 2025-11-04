#!/usr/bin/env python3
"""
Vectorbt backtest against cp_backtest_h (strict DB-only).
"""

import os
import argparse
from datetime import datetime, timedelta

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


def load_data(con, start, end, prices_table: str, signals_table: str):
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

    common = close.columns.intersection(bullish.columns).intersection(bearish.columns)
    close = close[common]
    bullish = bullish[common]
    bearish = bearish[common]
    return close, bullish, bearish


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


def run_vbt(close, bullish, bearish):
    import vectorbt as vbt
    entries = bullish >= 3
    exits = (bullish == 0) | (bearish <= -2)
    pf = vbt.Portfolio.from_signals(close, entries, exits, init_cash=100_000, fees=0.001, slippage=0.0005, cash_sharing=True, freq="1h")
    return pf


def parse_args():
    p = argparse.ArgumentParser(description="Vectorbt backtest against cp_backtest_h (strict)")
    p.add_argument("--start", type=str, help="UTC start datetime, e.g. 2025-02-13 00:00:00")
    p.add_argument("--end", type=str, help="UTC end datetime, e.g. 2025-11-04 06:00:00")
    p.add_argument("--days", type=int, default=int(os.getenv("BBACKTEST_DAYS", "30")), help="If no start/end, use last N days")
    p.add_argument("--db-name", type=str, default=os.getenv("DB_NAME_BT", "cp_backtest_h"))
    p.add_argument("--prices-table", type=str, default="ohlcv_1h_250_coins")
    p.add_argument("--signals-table", type=str, default="FE_DMV_ALL")
    p.add_argument("--list-ranges", action="store_true")
    return p.parse_args()


def main():
    load_dotenv()
    args = parse_args()

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

    eng = engine_for(args.db_name)
    with eng.connect() as con:
        if args.list_ranges:
            print_ranges(con, args.prices_table, args.signals_table)
            return
        close, bullish, bearish = load_data(con, start, end, args.prices_table, args.signals_table)

    print(f"Prices shape: {close.shape}")
    print(f"Signals shape: bullish={bullish.shape}, bearish={bearish.shape}")
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
    print(f"Filtered to columns with data: {len(nonnan_cols)} assets")

    print("\n== BACKTEST: RUN (vectorbt) ==")
    pf = run_vbt(close, bullish, bearish)

    print("\n== BACKTEST: STATS ==")
    print(pf.stats())


if __name__ == "__main__":
    main()


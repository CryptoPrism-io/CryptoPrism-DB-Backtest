#!/usr/bin/env python3
"""Inspect trade data structure."""

import os
import sys
from datetime import datetime, timedelta

import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))

from src.db import engine_for
from src.backtest import load_data, load_strategy, run_vbt


def main():
    load_dotenv()

    strategy_name = "SentimentLongShort_3_3"
    days = 30
    db_name = os.getenv("DB_NAME_BT", "cp_backtest_h")

    from src.backtest import load_strategy
    strategy = load_strategy(strategy_name)

    end_dt = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start_dt = end_dt - timedelta(days=days)
    start = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    eng = engine_for(db_name)
    with eng.connect() as con:
        close, bullish, bearish, ratios = load_data(
            con, start, end, "ohlcv_1h_250_coins", "FE_DMV_ALL",
            ratios_table="FE_RATIOS"
        )

    nonnan_cols = close.columns[close.notna().sum() > 20]
    close = close[nonnan_cols]
    bullish = bullish.reindex(columns=nonnan_cols, fill_value=0)
    bearish = bearish.reindex(columns=nonnan_cols, fill_value=0)

    if ratios:
        ratio_cols = nonnan_cols.intersection(ratios['beta'].columns)
        nonnan_cols = nonnan_cols.intersection(ratio_cols)
        close = close[nonnan_cols]
        bullish = bullish[nonnan_cols]
        bearish = bearish[nonnan_cols]
        for key in ratios:
            ratios[key] = ratios[key][nonnan_cols]

    pf = run_vbt(close, bullish, bearish, strategy=strategy, ratios=ratios)

    print("Inspecting trades structure...")
    print()

    # Check what's available
    print(f"pf.trades type: {type(pf.trades)}")
    print(f"pf.trades methods: {[x for x in dir(pf.trades) if not x.startswith('_')]}")
    print()

    # Try records_readable
    print("Checking records_readable...")
    try:
        rr = pf.trades.records_readable
        print(f"records_readable type: {type(rr)}")
        print(f"records_readable shape: {rr.shape if hasattr(rr, 'shape') else 'N/A'}")
        print(f"records_readable len: {len(rr)}")
        print()
        print("First entry:")
        if len(rr) > 0:
            print(rr.iloc[0])
            print()
            print("Entry type:", type(rr.iloc[0]))
            print("Entry keys/index:", rr.iloc[0].index.tolist() if hasattr(rr.iloc[0], 'index') else dir(rr.iloc[0]))
    except Exception as e:
        print(f"Error: {e}")

    # Try records
    print()
    print("Checking records...")
    try:
        records = pf.trades.records
        print(f"records type: {type(records)}")
        print(f"records: {records}")
    except Exception as e:
        print(f"Error: {e}")

    # Try get exit trades
    print()
    print("Checking get_exit_trades...")
    try:
        exit_trades = pf.trades.get_exit_trades()
        print(f"get_exit_trades type: {type(exit_trades)}")
        print(f"get_exit_trades: {exit_trades}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

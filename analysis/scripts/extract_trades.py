#!/usr/bin/env python3
"""Extract trades using vectorbt API."""

import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))

from src.db import engine_for
from src.backtest import load_data, load_strategy, run_vbt


def main():
    load_dotenv()

    strategy_name = "SentimentLongShort_3_3"
    days = 30
    db_name = os.getenv("DB_NAME_BT", "cp_backtest_h")

    # Load strategy
    from src.backtest import load_strategy
    strategy = load_strategy(strategy_name)

    # Time window
    end_dt = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start_dt = end_dt - timedelta(days=days)
    start = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    # Load data
    eng = engine_for(db_name)
    with eng.connect() as con:
        close, bullish, bearish, ratios = load_data(
            con, start, end, "ohlcv_1h_250_coins", "FE_DMV_ALL",
            ratios_table="FE_RATIOS"
        )

    # Filter data
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

    print(f"Strategy: {strategy.name}")
    print(f"Window: {start} -> {end}")
    print(f"Assets: {len(close.columns)}")
    print()

    # Run backtest
    pf = run_vbt(close, bullish, bearish, strategy=strategy, ratios=ratios)

    print("=" * 130)
    print("DETAILED TRADE REPORT - SentimentLongShort_3_3 Strategy")
    print("=" * 130)
    print()

    # Print stats first
    stats = pf.stats()
    print(f"Total Trades: {int(stats['Total Trades'])}")
    print(f"Win Rate: {stats['Win Rate [%]']:.1f}%")
    print(f"Total Return: {stats['Total Return [%]']:.2f}%")
    print(f"Best Trade: {stats['Best Trade [%]']:.2f}%")
    print(f"Worst Trade: {stats['Worst Trade [%]']:.2f}%")
    print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
    print()

    # Get trades using get_exit_trades
    try:
        # This returns a DataFrame with all closed trades
        trades = pf.trades.records_readable

        if trades is not None and len(trades) > 0:
            # Print each trade
            print("-" * 130)
            print("INDIVIDUAL TRADES")
            print("-" * 130)
            print()

            for idx, trade in enumerate(trades, 1):
                print(f"Trade #{idx}:")
                print(f"  Column (Asset Index): {trade['column']}")
                print(f"  Entry Index: {trade['entry_idx']:.0f}")
                print(f"  Entry Price: ${trade['entry_price']:.4f}")
                print(f"  Exit Index: {trade['exit_idx']:.0f}")
                print(f"  Exit Price: ${trade['exit_price']:.4f}")
                print(f"  Size: {trade['size']:.6f}")
                print(f"  PnL: ${trade['pnl']:.2f}")
                print(f"  Return: {trade['return']*100:.2f}%")
                print(f"  Trade Direction: {'LONG' if trade['size'] > 0 else 'SHORT'}")

                # Try to get asset name
                col_idx = int(trade['column'])
                if col_idx < len(close.columns):
                    asset = close.columns[col_idx]
                    entry_time = close.index[int(trade['entry_idx'])]
                    exit_time = close.index[int(trade['exit_idx'])]
                    print(f"  Asset: {asset}")
                    print(f"  Entry Time: {entry_time}")
                    print(f"  Exit Time: {exit_time}")
                    duration = int(trade['exit_idx']) - int(trade['entry_idx'])
                    print(f"  Duration: {duration} hours")

                print()

        else:
            print("No readable trade records found")
            print("\nTrying alternative approach...")
            print(f"Trades object type: {type(pf.trades)}")
            print(f"Trades dir: {[x for x in dir(pf.trades) if not x.startswith('_')]}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

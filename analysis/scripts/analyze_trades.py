#!/usr/bin/env python3
"""Analyze and report detailed trades from a backtest."""

import os
import sys
import argparse
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.db import engine_for
from src.backtest import load_data, load_strategy, run_vbt


def format_trade_report(pf, close, strategy_name="Unknown"):
    """
    Extract and format detailed trade information from portfolio.

    Returns a DataFrame with trade details.
    """
    print("\n" + "=" * 100)
    print(f"DETAILED TRADE REPORT: {strategy_name}")
    print("=" * 100 + "\n")

    # Get trades from portfolio
    # vectorbt stores trade info in the portfolio object
    trades_df = pf.trades.records_readable

    if trades_df.empty:
        print("No trades found in backtest.")
        return trades_df

    # Format the output
    trades_df = trades_df.copy()

    # Convert timestamp to datetime if needed
    if 'entry_idx' in trades_df.columns:
        # Get dates from close index
        print(f"Total Trades: {len(trades_df)}")
        print(f"Winning Trades: {(trades_df['pnl'] > 0).sum()}")
        print(f"Losing Trades: {(trades_df['pnl'] < 0).sum()}")
        print()

        # Display trades sorted by entry time
        trades_df = trades_df.sort_values('entry_idx')

        # Create readable version
        readable_trades = []
        for idx, row in trades_df.iterrows():
            entry_idx = int(row['entry_idx'])
            exit_idx = int(row['exit_idx'])

            # Try to get timestamps from close index
            try:
                entry_time = close.index[entry_idx]
                exit_time = close.index[exit_idx]
            except:
                entry_time = f"Index {entry_idx}"
                exit_time = f"Index {exit_idx}"

            # Get the asset/column name if available
            column = row.get('column', 'Unknown')

            trade_info = {
                'Asset': column,
                'Entry Time': entry_time,
                'Entry Price': f"${row['entry_price']:.2f}",
                'Exit Time': exit_time,
                'Exit Price': f"${row['exit_price']:.2f}",
                'Size': f"{row['size']:.6f}",
                'PnL': f"${row['pnl']:.2f}",
                'Return %': f"{row['return'] * 100:.2f}%",
                'Duration': f"{row['exit_idx'] - row['entry_idx']} hours",
            }
            readable_trades.append(trade_info)

        trades_display = pd.DataFrame(readable_trades)

        print("Individual Trades:")
        print("-" * 100)
        print(trades_display.to_string(index=False))
        print()

        # Summary stats
        print("Trade Summary Statistics:")
        print("-" * 100)
        print(f"Total PnL: ${trades_df['pnl'].sum():.2f}")
        print(f"Average PnL per Trade: ${trades_df['pnl'].mean():.2f}")
        print(f"Best Trade: ${trades_df['pnl'].max():.2f} ({trades_df['return'].max() * 100:.2f}%)")
        print(f"Worst Trade: ${trades_df['pnl'].min():.2f} ({trades_df['return'].min() * 100:.2f}%)")
        print(f"Average Duration: {trades_df['exit_idx'].sub(trades_df['entry_idx']).mean():.1f} hours")
        print()

        # Group by asset
        if 'column' in trades_df.columns:
            print("Trades by Asset:")
            print("-" * 100)
            asset_summary = trades_df.groupby('column').agg({
                'pnl': ['count', 'sum', 'mean'],
                'return': 'mean',
            }).round(4)
            asset_summary.columns = ['Num Trades', 'Total PnL', 'Avg PnL', 'Avg Return %']
            asset_summary['Avg Return %'] = asset_summary['Avg Return %'] * 100
            print(asset_summary.to_string())
            print()

    return trades_df


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Analyze detailed trades from backtest")
    parser.add_argument("--strategy", type=str, default="SentimentLongShort_3_3", help="Strategy name")
    parser.add_argument("--days", type=int, default=30, help="Number of days to backtest")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--coin", type=str, default=None, help="Single coin to analyze")
    parser.add_argument("--db-name", type=str, default=os.getenv("DB_NAME_BT", "cp_backtest_h"))
    args = parser.parse_args()

    # Load strategy
    try:
        from src.backtest import load_strategy
        strategy = load_strategy(args.strategy)
        print(f"Strategy: {strategy.name}")
        print(f"Description: {strategy.description}")
    except SystemExit:
        print(f"Strategy '{args.strategy}' not found.")
        return

    # Determine time window
    if args.start and args.end:
        start_dt = pd.to_datetime(args.start)
        end_dt = pd.to_datetime(args.end)
    else:
        end_dt = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        start_dt = end_dt - timedelta(days=args.days)

    start = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    print(f"Window: {start} -> {end}")

    # Load data
    eng = engine_for(args.db_name)
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

    # Filter to single coin if specified
    if args.coin:
        if args.coin not in close.columns:
            print(f"[ERROR] Coin '{args.coin}' not found in data")
            return
        close = close[[args.coin]]
        bullish = bullish[[args.coin]]
        bearish = bearish[[args.coin]]

    print(f"Assets: {len(close.columns)}")
    print(f"Data Points: {len(close)}")

    # Run backtest
    pf = run_vbt(close, bullish, bearish, strategy=strategy, ratios=ratios)

    # Print overall stats
    print("\n== PORTFOLIO STATS ==")
    print(pf.stats())

    # Print detailed trades
    trades_df = format_trade_report(pf, close, strategy.name)

    # Export to CSV if requested
    if not trades_df.empty:
        csv_file = f"trades_{args.strategy}_{args.days}d.csv"
        trades_df.to_csv(csv_file)
        print(f"\nTrades exported to: {csv_file}")


if __name__ == "__main__":
    main()

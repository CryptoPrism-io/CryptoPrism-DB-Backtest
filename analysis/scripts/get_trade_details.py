#!/usr/bin/env python3
"""Extract detailed trade information from backtest portfolio."""

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

    # Setup
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

    # Get trades
    print("=" * 120)
    print("DETAILED TRADE REPORT")
    print("=" * 120)
    print()

    # Access trades from portfolio
    try:
        # Get the trades object
        trades = pf.trades

        # Get the records (raw trade data)
        records = trades.records

        if records is not None and len(records) > 0:
            print(f"Total Trades: {len(records)}")

            # Create a readable trades dataframe
            trades_list = []

            for i, record in enumerate(records):
                entry_idx = int(record['entry_idx'])
                exit_idx = int(record['exit_idx'])
                col = int(record['col'])

                # Get asset name from column index
                asset_name = close.columns[col] if col < len(close.columns) else f"Asset_{col}"

                # Get times from index
                entry_time = close.index[entry_idx]
                exit_time = close.index[exit_idx]

                # Extract values
                entry_price = record['entry_price']
                exit_price = record['exit_price']
                size = record['size']
                pnl = record['pnl']
                return_pct = record['return']

                # Determine if long or short
                is_long = size > 0

                trades_list.append({
                    'Trade #': i + 1,
                    'Asset': asset_name,
                    'Type': 'LONG' if is_long else 'SHORT',
                    'Entry Time': entry_time,
                    'Entry Price': f"${entry_price:.4f}",
                    'Exit Time': exit_time,
                    'Exit Price': f"${exit_price:.4f}",
                    'Size': f"{abs(size):.6f}",
                    'Duration (hrs)': exit_idx - entry_idx,
                    'PnL': f"${pnl:.2f}",
                    'Return %': f"{return_pct * 100:.2f}%",
                })

            trades_df = pd.DataFrame(trades_list)

            print("\nAll Trades (Chronological Order):")
            print("-" * 120)
            print(trades_df.to_string(index=False))
            print()

            # Summary by trade type
            print("\nTrade Summary:")
            print("-" * 120)
            print(f"Total Trades: {len(records)}")

            # Count wins/losses
            wins = sum(1 for r in records if r['pnl'] > 0)
            losses = sum(1 for r in records if r['pnl'] < 0)
            print(f"Winning Trades: {wins} ({wins/len(records)*100:.1f}%)")
            print(f"Losing Trades: {losses} ({losses/len(records)*100:.1f}%)")
            print()

            # PnL stats
            pnls = [r['pnl'] for r in records]
            returns = [r['return'] for r in records]

            print(f"Total PnL: ${sum(pnls):.2f}")
            print(f"Average PnL per Trade: ${np.mean(pnls):.2f}")
            print(f"Best Trade: ${max(pnls):.2f} ({max(returns)*100:.2f}%)")
            print(f"Worst Trade: ${min(pnls):.2f} ({min(returns)*100:.2f}%)")
            print(f"Std Dev of Returns: {np.std(returns)*100:.2f}%")
            print()

            # Trade by asset
            asset_trades = {}
            for i, record in enumerate(records):
                col = int(record['col'])
                asset = close.columns[col] if col < len(close.columns) else f"Asset_{col}"
                if asset not in asset_trades:
                    asset_trades[asset] = {'count': 0, 'pnl': 0, 'wins': 0}
                asset_trades[asset]['count'] += 1
                asset_trades[asset]['pnl'] += record['pnl']
                if record['pnl'] > 0:
                    asset_trades[asset]['wins'] += 1

            print("Trades by Asset:")
            print("-" * 120)
            asset_df = pd.DataFrame([
                {
                    'Asset': asset,
                    'Count': stats['count'],
                    'Wins': stats['wins'],
                    'Win %': f"{stats['wins']/stats['count']*100:.1f}%",
                    'Total PnL': f"${stats['pnl']:.2f}"
                }
                for asset, stats in sorted(asset_trades.items(), key=lambda x: x[1]['pnl'], reverse=True)
            ])
            print(asset_df.to_string(index=False))
            print()

            # Long vs Short breakdown
            print("\nLong vs Short Analysis:")
            print("-" * 120)
            long_records = [r for r in records if r['size'] > 0]
            short_records = [r for r in records if r['size'] < 0]

            if long_records:
                long_pnl = sum(r['pnl'] for r in long_records)
                long_wins = sum(1 for r in long_records if r['pnl'] > 0)
                print(f"Long Trades:  {len(long_records)} trades, {long_wins} wins, ${long_pnl:.2f} PnL")
            else:
                print("Long Trades:  None")

            if short_records:
                short_pnl = sum(r['pnl'] for r in short_records)
                short_wins = sum(1 for r in short_records if r['pnl'] > 0)
                print(f"Short Trades: {len(short_records)} trades, {short_wins} wins, ${short_pnl:.2f} PnL")
            else:
                print("Short Trades: None")

            print()

            # Export to CSV
            trades_df.to_csv("detailed_trades.csv", index=False)
            print(f"Detailed trades exported to: detailed_trades.csv")

        else:
            print("No trades found.")

    except Exception as e:
        print(f"Error extracting trades: {e}")
        print(f"Exception type: {type(e)}")

        # Try alternative approach
        print("\nAttempting alternative trade extraction...")
        try:
            # Try to get trades from stats
            stats = pf.stats()
            print("\nPortfolio Stats:")
            print(stats)
        except Exception as e2:
            print(f"Error: {e2}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv


def eng(db):
    host = os.getenv("DB_HOST"); user = os.getenv("DB_USER"); pw = os.getenv("DB_PASSWORD"); port = os.getenv("DB_PORT", "5432")
    return create_engine(f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}")


def daily(con):
    q = """
    SELECT timestamp::date day, COUNT(*) rows, COUNT(DISTINCT slug) coins
    FROM ohlcv_1h_250_coins
    WHERE timestamp::date >= CURRENT_DATE - INTERVAL '2 days'
    GROUP BY 1 ORDER BY 1
    """
    return pd.read_sql(q, con, parse_dates=["day"]).assign(day=lambda d: d["day"].dt.date)


def latest(con):
    q = "SELECT MAX(timestamp) latest_ts FROM ohlcv_1h_250_coins"
    df = pd.read_sql(q, con, parse_dates=["latest_ts"]).fillna({"latest_ts": pd.NaT})
    return df["latest_ts"].iloc[0]


def main():
    load_dotenv()
    ai = os.getenv("DB_NAME", "cp_ai"); bt = os.getenv("DB_NAME_BT", "cp_backtest_h")
    a = eng(ai).connect(); b = eng(bt).connect()
    ai_d = daily(a).rename(columns={"rows":"rows_ai","coins":"coins_ai"})
    bt_d = daily(b).rename(columns={"rows":"rows_bt","coins":"coins_bt"})
    merged = (ai_d.merge(bt_d, on="day", how="outer").fillna(0))
    merged[["rows_ai","rows_bt","coins_ai","coins_bt"]] = merged[["rows_ai","rows_bt","coins_ai","coins_bt"]].astype(int)
    merged["delta_rows"] = merged["rows_ai"] - merged["rows_bt"]
    merged["delta_coins"] = merged["coins_ai"] - merged["coins_bt"]
    ai_ts = latest(a); bt_ts = latest(b)
    a.close(); b.close()
    print("\n== OHLCV Sync Check (last 3 days) ==")
    print(merged.to_string(index=False) if not merged.empty else "No rows")
    print("\nLatest:")
    print(f"  cp_ai:        {ai_ts}")
    print(f"  cp_backtest:  {bt_ts}")


if __name__ == "__main__":
    main()


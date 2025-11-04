#!/usr/bin/env python3
import os
from datetime import datetime, timedelta, timezone
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


def engine_for(db):
    host=os.getenv('DB_HOST'); user=os.getenv('DB_USER'); pw=os.getenv('DB_PASSWORD'); port=os.getenv('DB_PORT','5432')
    return create_engine(f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}")


def main():
    load_dotenv()
    ai=os.getenv('DB_NAME','cp_ai'); bt=os.getenv('DB_NAME_BT','cp_backtest_h')
    eng_ai=engine_for(ai); eng_bt=engine_for(bt)
    with eng_bt.connect() as con:
        latest = pd.read_sql("SELECT MAX(timestamp) latest_ts FROM ohlcv_1h_250_coins", con, parse_dates=['latest_ts'])['latest_ts'].iloc[0]
    if pd.isna(latest):
        end_dt = datetime.now(timezone.utc).replace(minute=59, second=59, microsecond=0)
        start_dt = end_dt - timedelta(days=3)
    else:
        start_dt = latest + timedelta(seconds=1)
        end_dt = datetime.now(timezone.utc).replace(minute=59, second=59, microsecond=0)
    if start_dt >= end_dt:
        print('[OK] Nothing to sync'); return
    q=text("""
      SELECT id,slug,name,symbol,timestamp,open,high,low,close,volume,market_cap
      FROM ohlcv_1h_250_coins WHERE timestamp>:s AND timestamp<=:e ORDER BY timestamp, slug
    """)
    with eng_ai.connect() as con:
        df = pd.read_sql(q, con, params={"s": start_dt, "e": end_dt}, parse_dates=['timestamp'])
    if df.empty:
        print('[OK] No incremental rows'); return
    tmp=f"ohlcv_1h_250_coins_tmp_{int(datetime.now().timestamp())}"
    with eng_bt.begin() as con:
        df.to_sql(tmp, con, if_exists='replace', index=False)
        ins=text(f"""
          INSERT INTO ohlcv_1h_250_coins (id,slug,name,symbol,timestamp,open,high,low,close,volume,market_cap)
          SELECT id,slug,name,symbol,timestamp,open,high,low,close,volume,market_cap FROM "{tmp}"
          ON CONFLICT (slug,timestamp) DO NOTHING
        """)
        res=con.execute(ins)
        con.execute(text(f'DROP TABLE "{tmp}"'))
        print(f"[OK] Inserted {res.rowcount if res.rowcount is not None else 0} rows")


if __name__=='__main__':
    main()


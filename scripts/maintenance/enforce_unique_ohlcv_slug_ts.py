#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


def main():
    load_dotenv()
    host=os.getenv('DB_HOST'); user=os.getenv('DB_USER'); pw=os.getenv('DB_PASSWORD'); port=os.getenv('DB_PORT','5432'); db=os.getenv('DB_NAME_BT','cp_backtest_h')
    eng=create_engine(f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db}")
    with eng.begin() as con:
        con.execute(text("""
        WITH d AS (
          SELECT ctid, ROW_NUMBER() OVER (PARTITION BY slug, timestamp ORDER BY ctid) rn
          FROM ohlcv_1h_250_coins
        )
        DELETE FROM ohlcv_1h_250_coins t USING d WHERE t.ctid=d.ctid AND d.rn>1;
        """))
        con.execute(text("""
        DO $$ BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid JOIN pg_namespace n ON n.oid=t.relnamespace
            WHERE n.nspname='public' AND t.relname='ohlcv_1h_250_coins' AND c.contype='u' AND c.conname='ohlcv_uniq_slug_ts')
          THEN
            ALTER TABLE public.ohlcv_1h_250_coins ADD CONSTRAINT ohlcv_uniq_slug_ts UNIQUE (slug,timestamp);
          END IF;
        END$$;
        """))
        con.execute(text("CREATE INDEX IF NOT EXISTS idx_ohlcv_ts ON ohlcv_1h_250_coins (timestamp)"))
        con.execute(text("CREATE INDEX IF NOT EXISTS idx_ohlcv_slug ON ohlcv_1h_250_coins (slug)"))
    print("[OK] Uniqueness enforced and indexes ensured")


if __name__ == '__main__':
    main()


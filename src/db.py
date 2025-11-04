import os
from sqlalchemy import create_engine


def engine_for(db_name: str):
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    pw = os.getenv("DB_PASSWORD")
    port = os.getenv("DB_PORT", "5432")
    if not host or not user or not pw:
        raise RuntimeError("Missing DB_HOST/DB_USER/DB_PASSWORD in environment")
    return create_engine(f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{db_name}")


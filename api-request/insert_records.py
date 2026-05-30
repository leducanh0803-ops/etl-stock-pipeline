import pandas as pd
import os
import yaml

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from get_data import mock_data


def get_config():

    with open("./docker-compose.yaml", "r") as f:
        return yaml.safe_load(f)


def create_engine_conn():
    print("Creating SQLAlchemy engine ...")
    
    user = os.environ.get("DB_USER", "db_user")
    password = os.environ.get("DB_PASSWORD", "db_password")
    db = os.environ.get("DB_NAME", "db")
    host = os.environ.get("DB_HOST", "postgres_container")
    
    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:5432/{db}"
    )
    return engine


def create_table(engine):

    print("Checking/Creating table ...")

    with engine.connect() as conn:

        conn.execute(text("""
            CREATE SCHEMA IF NOT EXISTS dev;
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dev.raw_ohlcv_data (
                ticker VARCHAR(20),
                volume FLOAT,
                vw_price FLOAT,
                open_price FLOAT,
                close_price FLOAT,
                high_price FLOAT,
                low_price FLOAT,
                ts TIMESTAMPTZ,
                no_txn BIGINT,
                inserted_at TIMESTAMP DEFAULT NOW()
            );
        """))

        conn.commit()

        print("Table ready")


def insert_records(engine, data):

    print("Inserting records ...")

    # convert list/dict response into dataframe
    df = pd.DataFrame(data)

    # rename columns
    df = df.rename(columns={
        'v': 'volume',
        'vw': 'vw_price',
        'o': 'open_price',
        'c': 'close_price',
        'h': 'high_price',
        'l': 'low_price',
        't': 'ts',
        'n': 'no_txn'
    })

    # add ticker column
    df['ticker'] = 'AAPL'

    # convert timestamp
    df['ts'] = pd.to_datetime(df['ts'], unit='ms', utc=True)

    # insert into postgres
    try:
        df.to_sql(
            name='raw_ohlcv_data',
            con=engine,
            schema='dev',
            if_exists='append',
            index=False
        )
    except SQLAlchemyError as e:
        print("Error while loading to the database: ", e)

    print("Records inserted successfully")


engine = create_engine_conn()

create_table(engine)

data = mock_data()

insert_records(engine, data)
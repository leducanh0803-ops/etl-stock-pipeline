import os
import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
from extractor import get_sp500_tickers

class Storage:
    """Handles storage of financial data using PostgreSQL and pandas."""

    def __init__(self):
        self.engine = self._create_engine()

    def _create_engine(self):
        """Create a SQLAlchemy engine from environment variables."""
        url = (
            f"postgresql+psycopg2://{os.getenv('DB_USER')}:"
            f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:5432/"
            f"{os.getenv('DB_NAME')}"
        )
        return create_engine(url, pool_pre_ping=True)

    def _create_loaded_table(self):
        """Create and populate the `dev.loaded_tickers` table if it doesn't exist."""
        create_query = """
            CREATE TABLE IF NOT EXISTS dev.loaded_tickers (
                id SERIAL,
                ticker VARCHAR(20) UNIQUE
            )
        """
        with self.engine.begin() as conn:
            print("Creating table for the first time....")
            conn.execute(text(create_query))
    
    def create_table_if_not_exists(self, table: str, df: pd.DataFrame, conflict_cols: list[str] = None):
        """Create a table based on pandas DataFrame schema if it doesn't exist, applying unique constraints."""
        dtype_map = {
            "object": "TEXT",
            "int64": "BIGINT",
            "int32": "INTEGER",
            "float64": "DOUBLE PRECISION",
            "float32": "REAL",
            "bool": "BOOLEAN",
            "datetime64[ns]": "TIMESTAMP",
            "datetime64[ns, UTC]": "TIMESTAMP",
        }

        cols = []
        for col, dtype in df.dtypes.items():
            pg_type = dtype_map.get(str(dtype), "TEXT")
            cols.append(f'"{col}" {pg_type}')
        
        #add time insert meta data

        cols.append("inserted_at TIMESTAMP DEFAULT NOW()")
        
        # Build the dynamic unique constraint if conflict columns are specified
        unique_constraint = ""
        if conflict_cols:
            quoted_conflicts = ", ".join([f'"{c}"' for c in conflict_cols])
            cols.append(f"UNIQUE ({quoted_conflicts})")

        sql = f"""
        CREATE TABLE IF NOT EXISTS {table} (
            {", ".join(cols)}
        )
        """
        with self.engine.begin() as conn:
            conn.execute(text(sql))

    def table_has_data(self, table: str, ticker: str) -> bool:
        """Check if a given ticker already exists in a table."""
        q = text(f"""
            SELECT 1
            FROM {table}
            WHERE ticker = :ticker
            LIMIT 1
        """)
        with self.engine.connect() as conn:
            return conn.execute(q, {"ticker": ticker}).fetchone() is not None

    def _format_ohlcv(self, raw_data, ticker):
        """Standardizes OHLCV data for both bootstrap and daily updates."""
        df = pd.DataFrame(raw_data)
        if df.empty:
            return df
            
        # Rename columns directly to Title Case to match your desired output
        df = df.rename(columns={
            "t": "date",         
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume",
            "vw":"weighted_volume"
        })

        # Convert epoch timestamp (ms) to a proper date
        df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True).dt.date
        df["ticker"] = ticker

        cols_to_keep = ["date", "ticker","open", "high", "low", "close", "volume","weighted_volume"]
        return df[cols_to_keep]


    def upsert(self, table: str, df: pd.DataFrame, conflict_cols: list[str]):
        # Pass conflict_cols down so they are baked into the table creation query
        self.create_table_if_not_exists(table, df, conflict_cols=conflict_cols)
        df = df.drop_duplicates(subset=conflict_cols, keep='last')
        if '.' in table:
            schema, table_name = table.split('.', 1)
        else:
            schema, table_name = None, table

        meta = MetaData()
        tbl = Table(table_name, meta, schema=schema, autoload_with=self.engine)

        rows = df.to_dict(orient='records')
        stmt = insert(tbl).values(rows)

        update_dict = {
            c.name: stmt.excluded[c.name]
            for c in tbl.columns
            if c.name not in conflict_cols
        }

        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_=update_dict,
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)
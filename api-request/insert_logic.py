from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
import polars as pl
import os

class Storage:
    def __init__(self):
        self.engine = self._create_engine()

    def _create_engine(self):
        url = (
            f"postgresql+psycopg2://{os.getenv('DB_USER')}:"
            f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:5432/"
            f"{os.getenv('DB_NAME')}"
        )
        return create_engine(url, pool_pre_ping=True)

    def table_has_data(self, table: str, ticker: str) -> bool:
        q = text(f"SELECT 1 FROM {table} WHERE ticker = :ticker LIMIT 1")
        with self.engine.connect() as conn:
            return conn.execute(q, {"ticker": ticker}).fetchone() is not None

    def write_append(self, table: str, df: pl.DataFrame):
        df.write_database(
            table_name=table,
            connection=self.engine,
            if_table_exists="append",
        )

    def upsert(self, table: str, df: pl.DataFrame, conflict_cols: list[str]):
        meta = MetaData()
        tbl = Table(table, meta, autoload_with=self.engine)

        rows = df.to_dicts()  

        stmt = insert(tbl).values(rows)

        update_dict = {
            c.name: stmt.excluded[c.name]
            for c in tbl.columns
            if c.name not in conflict_cols
        }

        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_=update_dict
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)
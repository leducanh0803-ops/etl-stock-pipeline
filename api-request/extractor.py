import requests
import os
import yfinance as yf
from yfinance import Ticker
import polars as pl
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import create_engine, text

load_dotenv()

API_KEY_MASSIVE = os.getenv('API_KEY_MASSIVE')
API_URL = os.getenv('API_URL')
TICKERS = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","JPM","WMT","XOM"]
class MassiveDailyExtractor:
    def __init__(self):

        self.api_key = API_KEY_MASSIVE
        self.base_url = API_URL
        self.params = {
            "apiKey": self.api_key
        }
        self.loading = self.is_loading()
    def is_loading(self):

        today = datetime.now().weekday()
        if today == 6 or today == 0:
            return False
        else: 
            return True
    
    def get_overview(self,ticker):
        endpoint = f"/v3/reference/tickers/{ticker}"
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url,params=self.params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("Error fetching data", e)
            raise
        else:
            data = response.json()['results']
            return data

    def get_ohlcv_data(self,
                       ticker):
        
        endpoint = f"/v2/aggs/ticker/{ticker}/prev"
        url = f"{self.base_url}{endpoint}"

        try: 
            response = requests.get(url,params=self.params)

        except requests.exceptions.RequestException as e:
            print("Error fetching data", e)
            raise
        
        else:
            data = response.json()['results']
            return data
        

class YFinanceFundamentalExtractor:

    def __init__(self, ticker):
        self.ticker = ticker
        self.client = Ticker(ticker)

    def col_name_clean(self,data):
        def _normalise(name: str) -> str:
            name = name.strip().lower()
            name = name.replace(' ','_')
            return name
        data = data.rename(columns = {col: _normalise(col) for col in data.columns})  
        data = data.reset_index(names = 'report_date')
        col_order = ['ticker']+data.columns
        data['ticker'] = self.ticker
        data = data[col_order]
        return data
    
    def get_historical_ohclv(self):
        return yf.download(self.ticker,
            period = 'max',
            interval='1d',
            auto_adjust=False,
            progress=False)

    def get_income_statement(self, quarterly=True):
        if quarterly:
            return self.col_name_clean(self.client.quarterly_income_stmt.T)
        return self.col_name_clean(self.client.income_stmt.T)

    def get_balance_sheet(self, quarterly=True):
        if quarterly:
            return self.col_name_clean(self.client.quarterly_balance_sheet.T)
        return self.col_name_clean(self.client.balance_sheet.T)

    def get_cashflow(self, quarterly=True):
        if quarterly:
            return self.col_name_clean(self.client.quarterly_cash_flow.T)
        return self.col_name_clean(self.client.cash_flow.T)
    

class Storage:
    def __init__(self):
        self.user     = os.environ.get("DB_USER")
        self.password = os.environ.get("DB_PASSWORD")
        self.host     = os.environ.get("DB_HOST")      
        self.db       = os.environ.get("DB_NAME")
        self.engine   = self._create_engine()

    # ── engine ───────────────────────────────────────────────────────────
    def _create_engine(self):
        url = f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:5432/{self.db}"
        return create_engine(url, pool_pre_ping=True)
        # pool_pre_ping=True → tests connection before using it from pool
        # prevents "connection closed" errors on idle connections

    # ── is_bootstrapped ──────────────────────────────────────────────────
    def is_bootstrapped(self, ticker: str, table: str) -> bool:
        """
        Answers: does this ticker already have rows in this table?

        True  → skip full history load, just do daily update
        False → run full bootstrap for this ticker
        """
        query = text(
            f"SELECT EXISTS (SELECT 1 FROM {table} WHERE ticker = :ticker LIMIT 1)"
            #              ↑ table interpolated directly — cannot be a SQL parameter
            #                                  ↑ ticker passed safely as parameter
        )
        try:
            with self.engine.connect() as conn:
                return conn.execute(query, {"ticker": ticker}).scalar()
        except Exception:
            return False      # table doesn't exist yet → treat as not bootstrapped

    # ── write ─────────────────────────────────────────────────────────────
    def write(self, table: str, df: pl.DataFrame) -> None:
        """
        Used for bootstrap (first time load).

        if_table_exists="append" means:
          - table missing → CREATE TABLE (infer schema from df) then INSERT
          - table exists  → INSERT directly, no schema change
        """
        df.write_database(
            table_name=table,
            connection=self.engine,
            if_table_exists="append",
        )

    # ── upsert ────────────────────────────────────────────────────────────
    def upsert(self, table: str, df: pl.DataFrame, conflict_cols: list[str]) -> None:
        """
        Used for daily incremental updates.

        INSERT ... ON CONFLICT (conflict_cols) DO UPDATE
        → if row exists (same ticker + date) → update it
        → if row is new                      → insert it
        → never creates duplicates
        """
        meta = MetaData()
        tbl  = Table(table, meta, autoload_with=self.engine)   # reads schema from DB
        rows = df.to_pandas().to_dict(orient="records")

        stmt = insert(tbl).values(rows)
        update_cols = {
            c.name: c
            for c in stmt.excluded          # EXCLUDED = the new row trying to be inserted
            if c.name not in conflict_cols  # don't update the conflict key itself
        }
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_=update_cols
        )
        with self.engine.begin() as conn:   
            conn.execute(upsert_stmt)       

   
    def read(self, table: str, ticker: str | None = None) -> pl.DataFrame:
        q = f"SELECT * FROM {table}"
        if ticker:
            q += " WHERE ticker = :ticker"
            return pl.read_database(
                text(q), self.engine,
                execute_options={"parameters": {"ticker": ticker}}
            )
        return pl.read_database(q, self.engine)



        
        
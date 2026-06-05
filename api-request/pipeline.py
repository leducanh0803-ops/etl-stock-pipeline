from extractor import MassiveDailyExtractor, get_sp500_tickers
from insert_logic import Storage
import time
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

class DataPipeline:
    def __init__(self):
        self.storage = Storage()
        self.massive = MassiveDailyExtractor()
        self.schema = os.getenv('DB_SCHEMA')

    def run(self):
        stocks = get_sp500_tickers()
        
        self.storage._create_loaded_table()
        for ticker in stocks:
            time.sleep(30)
            has_data = self.storage.table_has_data(f"{self.schema}.loaded_tickers", ticker)
            if not has_data:
                self.bootstrap(ticker)
                self.storage.upsert(f"{self.schema}.loaded_tickers", pd.DataFrame({ticker},columns=['ticker']),conflict_cols=['ticker'])
                print(f"--------LOADING {ticker} TO dev.ohlcv ---------------")
            self.daily_update(ticker)
    
    
    # ───────── BOOTSTRAP (FULL HISTORY ONCE) ─────────
    def bootstrap(self, ticker):
        raw_ohlcv = self.massive.upsert_ohlcv(ticker=ticker)
        clean_ohlcv = self.storage._format_ohlcv(raw_ohlcv, ticker)

        # OHLCV: unique per ticker + Date
        self.storage.upsert(f"{self.schema}.ohlcv", clean_ohlcv, conflict_cols=['ticker', 'date'])

    def daily_update(self, ticker):
        schema = os.getenv("DB_SCHEMA")
        if not self.massive.is_market_day():
            return

        # 1. Fetch raw data
        raw = self.massive.get_ohlcv_prev(ticker)
        if not raw:
            return
            
        # 2. Format it using the new helper
        df = self.storage._format_ohlcv(raw, ticker)

        self.storage.upsert(
            f"{schema}.ohlcv",
            df,
            conflict_cols=["ticker", "date"]
        )

def main():
    data_pipeline = DataPipeline()
    while True:
        data_pipeline.run()
        time.sleep(20)

if __name__ == "__main__":
    main()
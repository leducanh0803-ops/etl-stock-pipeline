from extractor import MassiveDailyExtractor, YFinanceFundamentalExtractor, get_sp500_tickers
from insert_logic import Storage
import time
import os
from dotenv import load_dotenv
load_dotenv()

class DataPipeline:
    def __init__(self):
        self.storage = Storage()
        self.massive = MassiveDailyExtractor()

    def run(self):
        tickers  = get_sp500_tickers()
        for ticker in tickers:

            has_data = self.storage.table_has_data("ohlcv", ticker)

            if not has_data:
                self.bootstrap(ticker)

            self.daily_update(ticker)

    # ───────── BOOTSTRAP (FULL HISTORY ONCE) ─────────
    def bootstrap(self,ticker):
        schema = os.getenv("DB_SCHEMA")
        ext = YFinanceFundamentalExtractor(ticker)

        self.storage.write_append(f"{schema}.ohlcv", ext.get_ohlcv())
        self.storage.write_append(f"{schema}.income_statement", ext.get_income_statement())
        self.storage.write_append(f"{schema}.balance_sheet", ext.get_balance_sheet())
        self.storage.write_append(f"{schema}.cashflow", ext.get_cashflow())

    # ───────── DAILY UPDATE ─────────
    def daily_update(self, ticker):

        if not self.massive.is_market_day():
            return

        raw = self.massive.get_ohlcv_prev(ticker)

        df = pl.DataFrame(raw).with_columns(
            pl.lit(ticker).alias("ticker")
        )

        self.storage.upsert(
            "ohlcv",
            df,
            conflict_cols=["ticker", "t"]
        ) 
    def quarterly_update(self,ticker):
        ext = YFinanceFundamentalExtractor(ticker)

        self.storage.upsert("income_statement",
                            ext.get_income_statement(),
                            conflict_cols=["ticker","report_date"])

        self.storage.upsert("balance_sheet", 
                                    ext.get_balance_sheet(),
                                    conflict_cols=["ticker","report_date"])

        self.storage.upsert("cashflow", 
                                  ext.get_cashflow(),
                                  conflict_cols=["ticker","report_date"])
def main():
    data_pipeline = DataPipeline()
    while True:
        data_pipeline.run()
        time.sleep(20)

if __name__ == "__main__":
    main()
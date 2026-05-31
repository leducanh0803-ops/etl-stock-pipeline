from extractor import MassiveDailyExtractor, YFinanceFundamentalExtractor
from storage import Storage
TICKERS = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","JPM","WMT","XOM"]


class DataPipeline:
    def __init__(self):
        self.storage = Storage()
        self.massive = MassiveDailyExtractor()

    def run(self, tickers=TICKERS):
        for ticker in tickers:

            has_data = self.storage.table_has_data("ohlcv", ticker)

            if not has_data:
                self.bootstrap(ticker)

            self.daily_update(ticker)

    # ───────── BOOTSTRAP (FULL HISTORY ONCE) ─────────
    def bootstrap(self, ticker):
        ext = YFinanceFundamentalExtractor(ticker)

        self.storage.write_append("ohlcv", ext.get_ohlcv())
        self.storage.write_append("income_statement", ext.get_income_statement())
        self.storage.write_append("balance_sheet", ext.get_balance_sheet())
        self.storage.write_append("cashflow", ext.get_cashflow())

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
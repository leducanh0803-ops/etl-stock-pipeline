import yfinance as yf
import polars as pl
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()


def get_sp500_tickers():
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"

    df = pd.read_csv(url)

    tickers = (
        df["Symbol"]
        .str.replace(".", "-", regex=False)
        .tolist()
    )
    return tickers

class MassiveDailyExtractor:
    def __init__(self):
        self.api_key = os.getenv("API_KEY_MASSIVE")
        self.base_url = os.getenv("API_URL")

    def is_market_day(self):
        # Mon–Fri only (simple version)
        return datetime.now().weekday() < 5

    def get_ohlcv_prev(self, ticker):
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/prev"

        r = requests.get(url, params={"apiKey": self.api_key})
        r.raise_for_status()
        return r.json()["results"]
    
    
    def _normalize_ticker_details(self,data: dict) -> pl.DataFrame:
        record = data.copy()

        address = record.pop("address", {})
        branding = record.pop("branding", {})

        record.update({
            "address1": address.get("address1"),
            "city": address.get("city"),
            "state": address.get("state"),
            "postal_code": address.get("postal_code"),
            "logo_url": branding.get("logo_url"),
            "icon_url": branding.get("icon_url"),
        })

        return pl.DataFrame([record])

    def get_overview(self, ticker):
        url = f"{self.base_url}/v3/reference/tickers/{ticker}"

        r = requests.get(url, params={"apiKey": self.api_key})
        r.raise_for_status()
        return self._normalize_ticker_details(r.json()["results"])


class YFinanceFundamentalExtractor:
    def __init__(self, ticker):
        self.ticker = ticker
        self.client = yf.Ticker(ticker)

    def _clean(self, df):
        df = df.T.reset_index().rename(columns={"index": "report_date"})
        df["ticker"] = self.ticker
        return pl.from_pandas(df)

    def get_ohlcv(self,):
        df = yf.download(self.ticker, period="max", interval="1d", progress=False)
        df = df.reset_index()
        df["ticker"] = self.ticker
        return pl.from_pandas(df)

    def get_income_statement(self):
        return self._clean(self.client.income_stmt)

    def get_balance_sheet(self):
        return self._clean(self.client.balance_sheet)

    def get_cashflow(self):
        return self._clean(self.client.cash_flow)
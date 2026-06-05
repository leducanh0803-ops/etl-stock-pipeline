import pandas as pd
import requests
from datetime import datetime,date
from dotenv import load_dotenv
import os

load_dotenv()

def get_sp500_tickers():
    """Fetch S&P 500 tickers from the official dataset, replacing dots with dashes."""
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    df = pd.read_csv(url)
    tickers = (
        df["Symbol"]
        .str.replace(".", "-", regex=False)
        .tolist()
    )
    return tickers


class MassiveDailyExtractor:
    """Extracts daily OHLCV and company overview data from Polygon.io."""

    def __init__(self):
        self.api_key = os.getenv("API_KEY_MASSIVE")
        self.base_url = os.getenv("API_URL")

    def is_market_day(self):
        """Simple market day check: returns True on Monday-Friday."""
        return datetime.now().weekday() < 5
    
    def upsert_ohlcv(self,ticker):
        """Get 2-year OHLCV data for a ticker"""
        today = date.today()
        start = today.replace(year=today.year-2)
        url= f"{self.base_url}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{today}"
        
        r = requests.get(url,params={"apiKey": self.api_key})
        r.raise_for_status()
        data = pd.DataFrame(r.json()['results'])
        data['t'] = pd.to_datetime(data['t'],unit='ms',utc=True)
        return data
        
    def get_ohlcv_prev(self, ticker):
        """Get previous day's OHLCV data for a ticker."""
        url = f"{self.base_url}/v2/aggs/ticker/{ticker}/prev"
        r = requests.get(url, params={"apiKey": self.api_key})
        r.raise_for_status()
        return r.json()["results"]

    def _normalize_ticker_details(self, data: dict) -> pd.DataFrame:
        """Flatten address and branding fields into a single-row DataFrame."""
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

        return pd.DataFrame([record])

    def get_overview(self, ticker):
        """Fetch company overview (ticker details) from Polygon.io."""
        url = f"{self.base_url}/v3/reference/tickers/{ticker}"
        r = requests.get(url, params={"apiKey": self.api_key})
        r.raise_for_status()
        return self._normalize_ticker_details(r.json()["results"])

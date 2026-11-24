"""Data layer: read and clean the saved data files (owner: Henry).

See the src/data_loader.py section of CONTRACT.md.
This is a stub: the names and types are final; the code comes in task H3.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# The repository's data/ folder. This file is in src/, so the repo root is two levels up.
DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"


class DataError(Exception):
    """Raised when a data file is missing or the data breaks a rule in CONTRACT.md."""


@dataclass(frozen=True, eq=False)  # eq=False: pandas tables can't be compared with ==
class Dataset:
    """The cleaned data: daily prices plus the list of stocks."""

    prices: pd.DataFrame  # DatetimeIndex named "Date", oldest first, one float column per ticker
    stocks: pd.DataFrame  # columns: ticker, name, sector, sector_source


class PriceProvider(ABC):
    """Where our price data comes from (D19). Every provider must have load()."""

    @abstractmethod
    def load(self) -> Dataset:
        """Return the cleaned and checked Dataset."""


class YahooFinanceProvider(PriceProvider):
    """Gets prices and company facts from Yahoo Finance (yfinance).

    Only scripts/download_data.py uses this class. The app uses CsvProvider.
    """

    def __init__(self, tickers: list[str], start: str, end: str) -> None:
        self.tickers = tickers
        self.start = start
        self.end = end  # yfinance does not include the end date itself

    def fetch(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Download the raw prices table and the raw stocks table."""
        import yfinance as yf  # here, not at the top: the app never needs yfinance

        raw = yf.download(
            self.tickers, start=self.start, end=self.end, auto_adjust=True, progress=False
        )
        prices = raw["Close"][self.tickers]  # adjusted close, one column per ticker
        prices = prices.rename_axis(index="Date", columns=None).sort_index()

        rows = []
        for ticker in self.tickers:
            info = yf.Ticker(ticker).info
            rows.append(
                {
                    "ticker": ticker,
                    "name": info.get("longName", ticker),
                    "sector": info.get("sector", ""),
                    "sector_source": "yfinance Ticker.info['sector']",
                }
            )
        stocks = pd.DataFrame(rows, columns=["ticker", "name", "sector", "sector_source"])
        return prices, stocks

    def load(self) -> Dataset:
        """Download, then clean and check (the cleaning comes in Part C)."""
        raise NotImplementedError("H3 Part C: clean what fetch() returns")


def load_dataset(data_dir: Path = DATA_DIR) -> Dataset:
    """Read data/prices.csv and data/stocks.csv, clean them, and check the rules.

    Cleaning: drop days where every price is missing; forward-fill a gap of at
    most 2 trading days; drop a ticker that is missing more than 5% of days.

    Raises DataError with a clear message if a file is missing, or if there are
    more than 20 tickers, fewer than 3 sectors, or fewer than 200 trading days.
    """
    raise NotImplementedError("H3 (Henry): due Tue 11/24, 12:00 PM")

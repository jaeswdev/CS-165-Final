"""Data layer: get, clean, and check the price data (owner: Henry).

See the src/data_loader.py section of CONTRACT.md (decisions D2, D18, and D19).
- PriceProvider: the interface that every data source follows.
- CsvProvider: reads the saved files in data/. The app uses only this provider.
- YahooFinanceProvider: downloads from Yahoo Finance. Only scripts/download_data.py uses it.
- clean_dataset: the one cleaning function that both providers use.
"""

import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# The repository's data/ folder. This file is in src/, so the repo root is two levels up.
DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"

# The cleaning and checking rules from CONTRACT.md.
MAX_FILL_DAYS = 2  # fill a gap of at most 2 trading days
MAX_MISSING_SHARE = 0.05  # drop a ticker that is missing more than 5% of the days
MAX_TICKERS = 20  # section 3: at most 20 stocks
MIN_SECTORS = 3  # section 3: at least 3 sectors
MIN_TRADING_DAYS = 200  # about one year of prices
STOCK_COLUMNS = ["ticker", "name", "sector", "sector_source"]


class DataError(Exception):
    """Raised when a data file is missing or the data breaks a rule in CONTRACT.md."""


@dataclass(frozen=True, eq=False)  # eq=False: pandas tables can't be compared with ==
class Dataset:
    """The cleaned data: daily prices plus the list of stocks."""

    prices: pd.DataFrame  # DatetimeIndex named "Date", oldest first, one float column per ticker
    stocks: pd.DataFrame  # columns: ticker, name, sector, sector_source


def clean_dataset(prices: pd.DataFrame, stocks: pd.DataFrame) -> Dataset:
    """Clean the raw tables, check the rules, and return a Dataset.

    Both providers use this one function, so the rules are the same everywhere.
    prices: one row per day (the dates are the index) and one column per ticker.
    stocks: the columns ticker, name, sector, and sector_source.

    Cleaning steps, in this order (CONTRACT.md, D18):
    1. A price that is blank, text, zero, negative, or infinite counts as missing.
    2. Drop the days where every price is missing.
    3. Fill a gap of at most 2 trading days with the last known price.
       Longer gaps are not filled.
    4. Drop a ticker that is still missing more than 5% of the days (with a warning).
    5. Drop the days where a remaining ticker still has no price, so every stock
       has a price on every day.
    Prices keep their full decimals: nothing is rounded.

    Raises DataError if there are more than 20 tickers, fewer than 3 sectors,
    or fewer than 200 trading days, or if a ticker has no row in the stocks table.
    """
    clean_prices = _clean_prices(prices)
    clean_stocks = _match_stocks(stocks, list(clean_prices.columns))
    _check_rules(clean_prices, clean_stocks)
    return Dataset(prices=clean_prices, stocks=clean_stocks)


def _clean_prices(raw: pd.DataFrame) -> pd.DataFrame:
    """Steps 1 to 5 of clean_dataset, for the prices table."""
    prices = raw.copy()
    if not isinstance(prices.index, pd.DatetimeIndex):
        try:
            prices.index = pd.to_datetime(prices.index, format="%Y-%m-%d")
        except (ValueError, TypeError) as error:
            raise DataError(f"A date in the prices table is not YYYY-MM-DD: {error}") from error
    prices = prices.rename_axis(index="Date", columns=None).sort_index()

    # 1. Bad prices count as missing (D18).
    prices = prices.apply(pd.to_numeric, errors="coerce").astype(float)  # blank, text
    prices = prices.where((prices > 0) & np.isfinite(prices))  # zero, negative, infinite

    # 2. Drop the days where every price is missing.
    prices = prices.dropna(how="all")

    # 3. Fill a gap of at most 2 trading days with the last known price.
    prices = _fill_short_gaps(prices, MAX_FILL_DAYS)

    # 4. Drop a ticker that is still missing more than 5% of the days.
    missing_share = prices.isna().mean()
    for ticker in missing_share[missing_share > MAX_MISSING_SHARE].index:
        warnings.warn(
            f"Dropped {ticker}: {missing_share[ticker]:.1%} of its days have no price "
            f"(more than {MAX_MISSING_SHARE:.0%}). Note this in data/README.md.",
            stacklevel=3,
        )
        prices = prices.drop(columns=ticker)

    # 5. Drop the days where a remaining ticker still has no price.
    return prices.dropna(how="any")


def _fill_short_gaps(prices: pd.DataFrame, max_days: int) -> pd.DataFrame:
    """Forward-fill each gap of at most max_days missing days. Leave longer gaps missing."""
    filled = prices.copy()
    for ticker in prices.columns:
        column = prices[ticker]
        missing = column.isna()
        run_id = missing.ne(missing.shift(fill_value=False)).cumsum()  # new number at each change
        run_length = missing.groupby(run_id).transform("size")  # how long each run is
        short_gap = missing & (run_length <= max_days)
        filled[ticker] = column.where(~short_gap, column.ffill())
    return filled


def _match_stocks(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Keep one stocks row per ticker in prices, in the same order as the price columns."""
    missing_columns = [column for column in STOCK_COLUMNS if column not in raw.columns]
    if missing_columns:
        raise DataError(f"The stocks table has no {', '.join(missing_columns)} column.")
    stocks = raw[STOCK_COLUMNS].drop_duplicates(subset="ticker").set_index("ticker")
    no_facts = [ticker for ticker in tickers if ticker not in stocks.index]
    if no_facts:
        raise DataError(f"The stocks table has no name or sector for {', '.join(no_facts)}.")
    return stocks.loc[tickers].reset_index()


def _check_rules(prices: pd.DataFrame, stocks: pd.DataFrame) -> None:
    """Raise DataError if the cleaned data breaks a rule in CONTRACT.md."""
    if len(prices.columns) > MAX_TICKERS:
        raise DataError(f"{len(prices.columns)} tickers: section 3 allows at most {MAX_TICKERS}.")
    sectors = sorted(stocks["sector"].dropna().unique())
    if len(sectors) < MIN_SECTORS:
        raise DataError(
            f"Only {len(sectors)} sector(s) after cleaning ({', '.join(sectors)}): "
            f"we need at least {MIN_SECTORS}."
        )
    if len(prices) < MIN_TRADING_DAYS:
        raise DataError(
            f"Only {len(prices)} trading days after cleaning: we need at least {MIN_TRADING_DAYS}."
        )


class PriceProvider(ABC):
    """Where our price data comes from (D19). Every provider must have load()."""

    @abstractmethod
    def load(self) -> Dataset:
        """Return the cleaned and checked Dataset."""


class CsvProvider(PriceProvider):
    """Reads the saved files data/prices.csv and data/stocks.csv.

    The app uses only this provider, so it works offline and gives the same
    numbers every time (D2).
    """

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir = Path(data_dir)

    def load(self) -> Dataset:
        """Read both files, then clean and check them with clean_dataset."""
        prices_file = self.data_dir / "prices.csv"
        stocks_file = self.data_dir / "stocks.csv"
        for file in (prices_file, stocks_file):
            if not file.exists():
                raise DataError(f"Missing data file: {file}. Run: python scripts/download_data.py")
        try:
            prices = pd.read_csv(prices_file)  # reads every price back exactly (full decimals)
            stocks = pd.read_csv(stocks_file, dtype=str)
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as error:
            raise DataError(f"Cannot read the data files in {self.data_dir}: {error}") from error
        if "Date" not in prices.columns:
            raise DataError(f"{prices_file} has no Date column.")
        return clean_dataset(prices.set_index("Date"), stocks)


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
        """Download with fetch(), then clean and check with clean_dataset."""
        prices, stocks = self.fetch()
        return clean_dataset(prices, stocks)


def load_dataset(data_dir: Path = DATA_DIR) -> Dataset:
    """Read, clean, and check the saved data in data_dir. This is how the app gets its data.

    Returns CsvProvider(data_dir).load(). See clean_dataset for the cleaning steps
    and the DataError checks.
    """
    return CsvProvider(data_dir).load()

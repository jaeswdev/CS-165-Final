"""Data layer: read and clean the saved data files (owner: Henry).

See the src/data_loader.py section of CONTRACT.md.
This is a stub: the names and types are final; the code comes in task H3.
"""

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


def load_dataset(data_dir: Path = DATA_DIR) -> Dataset:
    """Read data/prices.csv and data/stocks.csv, clean them, and check the rules.

    Cleaning: drop days where every price is missing; forward-fill a gap of at
    most 2 trading days; drop a ticker that is missing more than 5% of days.

    Raises DataError with a clear message if a file is missing, or if there are
    more than 20 tickers, fewer than 3 sectors, or fewer than 200 trading days.
    """
    raise NotImplementedError("H3 (Henry): due Tue 11/24, 12:00 PM")

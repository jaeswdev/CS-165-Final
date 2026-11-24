"""Logic layer: returns and portfolio math (owner: Henry).

See the src/analysis.py section of CONTRACT.md and section 3 of the instructions.
This is a stub: the names and types are final; the code comes in task H4.
Only this module calls the data layer (src/data_loader.py).
"""

from pathlib import Path

import pandas as pd

from src.data_loader import DATA_DIR, Dataset, load_dataset  # load_dataset is used in H4
from src.models import StockStats

TRADING_DAYS = 252  # trading days in one year, used to annualize volatility


def historical_return(start_price: float, end_price: float) -> float:
    """Return (end_price - start_price) / start_price, as a fraction.

    Raises ValueError if start_price <= 0.
    """
    raise NotImplementedError("H4 (Henry): due Tue 11/24, 9:00 PM")


def annualized_volatility(prices: pd.Series) -> float:
    """Return the standard deviation of daily percent changes times sqrt(TRADING_DAYS)."""
    raise NotImplementedError("H4 (Henry): due Tue 11/24, 9:00 PM")


def compute_stock_stats(dataset: Dataset) -> list[StockStats]:
    """Return one StockStats per ticker, sorted by ticker.

    The start values come from the first row of the window and the end values
    from the last row.
    """
    raise NotImplementedError("H4 (Henry): due Tue 11/24, 9:00 PM")


def load_stock_stats(data_dir: Path = DATA_DIR) -> list[StockStats]:
    """Call load_dataset(data_dir), then compute_stock_stats.

    This is the only logic function that reads files.
    """
    raise NotImplementedError("H4 (Henry): due Tue 11/24, 9:00 PM")


def portfolio_return(weights: dict[str, float], returns: dict[str, float]) -> float:
    """Return the sum of weight x return over the tickers in weights.

    Raises ValueError if the weights do not add up to 1 (within 1e-6) or if a
    ticker in weights has no return.
    """
    raise NotImplementedError("H4 (Henry): due Tue 11/24, 9:00 PM")


def final_value(amount: float, port_return: float) -> float:
    """Return round(amount x (1 + port_return), 2), in dollars."""
    raise NotImplementedError("H4 (Henry): due Tue 11/24, 9:00 PM")


def allocate_dollars(weights: dict[str, float], amount: float) -> dict[str, float]:
    """Split amount by weights into dollars per ticker, exact to the cent.

    Work in whole cents: each ticker gets floor(weight x total cents). The
    leftover cents (at most 3) go to the largest weight (tie: first ticker A-Z),
    so the dollars add up to the amount exactly.
    """
    raise NotImplementedError("H4 (Henry): due Tue 11/24, 9:00 PM")

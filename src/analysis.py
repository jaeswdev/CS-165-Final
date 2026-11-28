"""Logic layer: returns, volatility, and portfolio math (owner: Henry).

See the src/analysis.py section of CONTRACT.md and section 3 of the instructions.
Only this module calls the data layer (src/data_loader.py), and only inside
load_stock_stats. Every other function is pure: it uses only its inputs.

Units: returns, weights, and volatility are fractions (0.1234 means 12.34%).
Money is in dollars. We keep all the decimals and round only money, to cents.
"""

import math
from pathlib import Path

import pandas as pd

from src.data_loader import DATA_DIR, Dataset, load_dataset
from src.models import StockStats

TRADING_DAYS = 252  # trading days in one year, used to annualize volatility
WEIGHT_TOLERANCE = 1e-6  # CONTRACT.md: the weights must add up to 1 within this amount


def historical_return(start_price: float, end_price: float) -> float:
    """Return (end_price - start_price) / start_price, as a fraction.

    Section 3 of the instructions: how much the price went up or down over the
    window, compared with the start price. Example: $100 -> $112 gives 0.12 (12%).

    Raises ValueError if start_price is 0 or less (or not a number), because
    we cannot divide by it.
    """
    if not start_price > 0:  # "not ... > 0" also refuses nan
        raise ValueError(f"The start price must be more than 0, got {start_price}.")
    return (end_price - start_price) / start_price


def annualized_volatility(prices: pd.Series) -> float:
    """Return the standard deviation of daily percent changes times sqrt(TRADING_DAYS).

    Volatility shows how much a price jumps up and down from day to day, as a
    yearly number. Three steps:
    1. Daily percent change: today's price / yesterday's price - 1.
    2. The standard deviation of those changes, as a sample: divide by n - 1.
       This is the pandas default and the usual choice for past data.
    3. Multiply by sqrt(252), because a year has about 252 trading days.
    Example: 100 -> 110 -> 99 has changes of +10% and -10%, so
    sqrt((0.10^2 + 0.10^2) / (2 - 1)) x sqrt(252) = 0.1414 x 15.87 = 2.2450.

    Raises ValueError if there are fewer than 2 prices, or if a price is missing,
    0, or negative. (The data loader removes those, so this should not happen.)
    """
    values = pd.Series(prices, dtype=float)
    if len(values) < 2:
        raise ValueError("Volatility needs at least 2 prices.")
    if not ((values > 0) & (values < math.inf)).all():  # also refuses nan
        raise ValueError("Every price must be a number more than 0 to compute volatility.")
    daily_changes = values.pct_change().dropna()
    return float(daily_changes.std(ddof=1) * math.sqrt(TRADING_DAYS))


def compute_stock_stats(dataset: Dataset) -> list[StockStats]:
    """Return one StockStats per ticker, sorted by ticker (A-Z).

    The start values come from the first row of the window and the end values
    from the last row. The name and sector come from the stocks table (the
    company facts), and the prices come from the prices table.

    Raises ValueError if the prices table is empty, or if a ticker has no row
    in the stocks table.
    """
    prices = dataset.prices
    if prices.empty:
        raise ValueError("The prices table is empty.")
    facts = dataset.stocks.set_index("ticker")
    start_date = pd.Timestamp(prices.index[0]).strftime("%Y-%m-%d")
    end_date = pd.Timestamp(prices.index[-1]).strftime("%Y-%m-%d")

    stats = []
    for ticker in sorted(prices.columns):  # the price columns are in sector order, not A-Z
        if ticker not in facts.index:
            raise ValueError(f"The stocks table has no name or sector for {ticker}.")
        column = prices[ticker]
        start_price = float(column.iloc[0])
        end_price = float(column.iloc[-1])
        stats.append(
            StockStats(
                ticker=ticker,
                name=str(facts.at[ticker, "name"]),
                sector=str(facts.at[ticker, "sector"]),
                start_date=start_date,
                end_date=end_date,
                start_price=start_price,
                end_price=end_price,
                hist_return=historical_return(start_price, end_price),
                volatility=annualized_volatility(column),
            )
        )
    return stats


def load_stock_stats(data_dir: Path = DATA_DIR) -> list[StockStats]:
    """Call load_dataset(data_dir), then compute_stock_stats.

    This is the only logic function that reads files (CONTRACT.md).
    app.py calls it once and caches the result.
    """
    return compute_stock_stats(load_dataset(data_dir))


def _check_weights(weights: dict[str, float]) -> None:
    """Raise ValueError unless the weights add up to 1 (within WEIGHT_TOLERANCE)."""
    total = math.fsum(weights.values())
    if abs(total - 1) > WEIGHT_TOLERANCE:
        raise ValueError(f"The weights must add up to 1 (100%), but they add up to {total}.")


def portfolio_return(weights: dict[str, float], returns: dict[str, float]) -> float:
    """Return the sum of weight x return over the tickers in weights.

    Section 3 of the instructions: the portfolio return is the weighted sum of
    the stock returns. Example: weights 40/30/20/10 and returns 10%, 5%, -2%,
    and 20% give 0.4 x 0.10 + 0.3 x 0.05 + 0.2 x (-0.02) + 0.1 x 0.20 = 0.071 (7.1%).
    math.fsum adds the parts without rounding errors piling up, so the order of
    the tickers never changes the answer. Returns for tickers that are not in
    weights (the other stocks in the table) are ignored.

    Raises ValueError if the weights do not add up to 1 (within 1e-6), or if a
    ticker in weights has no return.
    """
    _check_weights(weights)
    missing = sorted(ticker for ticker in weights if ticker not in returns)
    if missing:
        raise ValueError(f"No return for {', '.join(missing)}.")
    return math.fsum(weight * returns[ticker] for ticker, weight in weights.items())


def final_value(amount: float, port_return: float) -> float:
    """Return round(amount x (1 + port_return), 2), in dollars.

    The money at the end of the window, if the portfolio had been bought at
    the start. Example: $10,000 with a 7.1% return gives $10,710.00.
    Only the money is rounded (to cents); the return keeps all its decimals.
    """
    return round(amount * (1 + port_return), 2)


def allocate_dollars(weights: dict[str, float], amount: float) -> dict[str, float]:
    """Split amount by weights into dollars per ticker, exact to the cent.

    Work in whole cents: each ticker gets floor(weight x total cents). The
    leftover cents (at most 3 for 4 stocks) go to the largest weight (tie: the
    first ticker A-Z), so the dollars add up to the amount exactly.
    Example: $999.99 = 99,999 cents at 30/30/20/20 gives 29,999 + 29,999 +
    19,999 + 19,999 = 99,996 cents. The 3 leftover cents go to the first 30%
    ticker, so it gets $300.02.

    Two computer-math traps are handled on purpose:
    - round(amount x 100), not int(): 4.35 x 100 is 434.99999999999994 in a computer.
    - The product is rounded to 6 decimals before floor: 0.29 x 100,000 is
      28,999.999999999996 in a computer, but the right answer is 29,000.

    Raises ValueError if the weights do not add up to 1 (within 1e-6).
    """
    _check_weights(weights)
    total_cents = round(amount * 100)
    cents = {
        ticker: math.floor(round(weight * total_cents, 6)) for ticker, weight in weights.items()
    }
    largest = min(weights, key=lambda ticker: (-weights[ticker], ticker))
    cents[largest] += total_cents - sum(cents.values())
    return {ticker: cents[ticker] / 100 for ticker in weights}

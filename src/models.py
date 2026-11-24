"""Shared data shapes for the Stock Portfolio Suggestion Engine (see CONTRACT.md).

Every module passes data around in these five types.
Units: returns, weights, volatility, and drop are fractions (0.1234 means 12.34%).
Money is in dollars, rounded to cents.

This file holds data only: no calculations, no checks, and no imports from
other src modules, because every module imports this one.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StockStats:
    """One stock's facts and results for the one-year window."""

    ticker: str          # for example "AAPL"
    name: str            # company name, for example "Apple Inc."
    sector: str          # sector label from yfinance, for example "Technology"
    start_date: str      # first trading day used, "YYYY-MM-DD"
    end_date: str        # last trading day used, "YYYY-MM-DD"
    start_price: float   # adjusted close on start_date, in dollars
    end_price: float     # adjusted close on end_date, in dollars
    hist_return: float   # (end_price - start_price) / start_price, a fraction
    volatility: float    # annualized standard deviation of daily returns, a fraction


@dataclass(frozen=True)
class Holding:
    """One of the 4 stocks in a suggested portfolio."""

    ticker: str
    name: str
    sector: str
    weight: float        # share of the money, a fraction; the 4 weights add up to 1
    dollars: float       # money put in this stock, in dollars, rounded to cents
    hist_return: float   # this stock's historical return, a fraction


@dataclass(frozen=True)
class Portfolio:
    """A suggested portfolio for one amount and one risk profile."""

    profile: str                   # "Conservative", "Balanced", or "Growth"
    amount: float                  # the amount invested, in dollars
    holdings: tuple[Holding, ...]  # exactly 4 (checked in strategy.check_rules, not here)
    portfolio_return: float        # weighted sum of the holdings' returns, a fraction
    final_value: float             # amount * (1 + portfolio_return), in dollars, rounded to cents
    why_selected: str              # plain-English reason these 4 stocks were chosen
    profile_effect: str            # plain-English text on how the risk profile changed the choice


@dataclass(frozen=True)
class Comparison:
    """Our suggestion compared with an equal-weight portfolio of the same 4 stocks."""

    suggested_return: float        # a fraction
    suggested_final_value: float   # in dollars
    equal_return: float            # a fraction, each stock at 25%
    equal_final_value: float       # in dollars
    difference: float              # suggested_final_value - equal_final_value, in dollars


@dataclass(frozen=True)
class Scenario:
    """What happens if every chosen stock falls by the same percent."""

    drop: float                    # the fall, a fraction (0.10 means 10%)
    base_value: float              # the amount invested, in dollars
    loss: float                    # base_value * drop, in dollars, rounded to cents
    remaining_value: float         # base_value - loss, in dollars
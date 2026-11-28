"""Tests for src/models.py, the shared data classes (task H1).

They check what our dataclasses promise: they keep the values we give them,
two objects with the same values are equal, and nothing can change after an
object is made (frozen). All numbers here are made up.
"""

import dataclasses

import pytest

from src.models import Holding, Portfolio, StockStats

pytestmark = pytest.mark.unit

def make_holding(ticker: str = "AAPL", weight: float = 0.25) -> Holding:
    """Build a small Holding for the tests."""
    return Holding(
        ticker=ticker,
        name="Example Company",
        sector="Technology",
        weight=weight,
        dollars=2500.00,
        hist_return=0.12,
    )


def test_stock_stats_keeps_its_values():
    stats = StockStats(
        ticker="XOM",
        name="Example Energy Company",
        sector="Energy",
        start_date="2025-11-18",
        end_date="2026-11-18",
        start_price=100.0,
        end_price=112.0,
        hist_return=0.12,
        volatility=0.25,
    )
    assert stats.ticker == "XOM"
    assert stats.sector == "Energy"
    assert stats.hist_return == pytest.approx(0.12)


def test_same_values_make_equal_objects():
    assert make_holding() == make_holding()
    assert make_holding() != make_holding(weight=0.30)
    # Equal frozen objects also have the same hash, so a set keeps only one of them.
    assert len({make_holding(), make_holding()}) == 1


def test_frozen_objects_cannot_change():
    holding = make_holding()
    portfolio = Portfolio(
        profile="Balanced",
        amount=10000.00,
        holdings=(holding, make_holding("MSFT"), make_holding("JNJ"), make_holding("XOM")),
        portfolio_return=0.12,
        final_value=11200.00,
        why_selected="Example text.",
        profile_effect="Example text.",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        holding.weight = 0.5
    with pytest.raises(dataclasses.FrozenInstanceError):
        portfolio.amount = 1.0
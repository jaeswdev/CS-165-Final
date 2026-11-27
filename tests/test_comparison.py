"""Tests for src/comparison.py (task C3): the equal-weight comparison and the drop scenario.

compare_equal_weight uses analysis.portfolio_return and analysis.final_value (Henry, H4).
So these tests do not depend on H4 being finished, a fixture swaps in small stand-ins
that follow the formulas in CONTRACT.md. All numbers here are made up and easy to
check by hand.
Every test has exactly one marker from pytest.ini (D21).
"""

import math

import pytest

from src import analysis
from src.comparison import compare_equal_weight, decline_scenario
from src.models import Comparison, Holding, Portfolio, Scenario


def contract_portfolio_return(weights, returns):
    """Stand-in for analysis.portfolio_return, written straight from CONTRACT.md."""
    if abs(sum(weights.values()) - 1) > 1e-6:
        raise ValueError("weights must add up to 1")
    return sum(weight * returns[ticker] for ticker, weight in weights.items())


def contract_final_value(amount, port_return):
    """Stand-in for analysis.final_value, written straight from CONTRACT.md."""
    return round(amount * (1 + port_return), 2)


@pytest.fixture(autouse=True)
def use_contract_math(monkeypatch):
    """Swap in the stand-ins and count how often comparison.py calls them."""
    calls = []

    def portfolio_return(weights, returns):
        calls.append("portfolio_return")
        return contract_portfolio_return(weights, returns)

    def final_value(amount, port_return):
        calls.append("final_value")
        return contract_final_value(amount, port_return)

    monkeypatch.setattr(analysis, "portfolio_return", portfolio_return)
    monkeypatch.setattr(analysis, "final_value", final_value)
    return calls


# The 4 made-up stocks: ticker, sector, weight in our suggestion, historical return.
STOCKS = [
    ("AAA", "Technology", 0.40, 0.40),
    ("BBB", "Technology", 0.30, 0.20),
    ("CCC", "Healthcare", 0.20, 0.10),
    ("DDD", "Energy", 0.10, -0.10),
]


def make_portfolio(amount=10_000.00, stocks=STOCKS):
    """Build a Portfolio the way suggest_portfolio would, using the contract math."""
    weights = {ticker: weight for ticker, _, weight, _ in stocks}
    returns = {ticker: ret for ticker, _, _, ret in stocks}
    port_return = contract_portfolio_return(weights, returns)
    holdings = tuple(
        Holding(
            ticker=ticker,
            name=f"{ticker} Inc.",
            sector=sector,
            weight=weight,
            dollars=round(amount * weight, 2),
            hist_return=ret,
        )
        for ticker, sector, weight, ret in stocks
    )
    return Portfolio(
        profile="Growth",
        amount=amount,
        holdings=holdings,
        portfolio_return=port_return,
        final_value=contract_final_value(amount, port_return),
        why_selected="Made-up text.",
        profile_effect="Made-up text.",
    )


# ---------- unit: one function on its own ----------


@pytest.mark.unit
def test_equal_weight_puts_25_percent_in_each_stock():
    # Equal return = 0.25 x (0.40 + 0.20 + 0.10 - 0.10) = 0.15
    result = compare_equal_weight(make_portfolio())
    assert isinstance(result, Comparison)
    assert result.equal_return == pytest.approx(0.15)
    assert result.equal_final_value == 11_500.00


@pytest.mark.unit
def test_suggested_side_comes_from_the_portfolio():
    # Suggested return = 0.4x0.40 + 0.3x0.20 + 0.2x0.10 + 0.1x(-0.10) = 0.23
    portfolio = make_portfolio()
    result = compare_equal_weight(portfolio)
    assert result.suggested_return == pytest.approx(0.23)
    assert result.suggested_return == portfolio.portfolio_return
    assert result.suggested_final_value == portfolio.final_value == 12_300.00


@pytest.mark.unit
def test_difference_is_suggested_minus_equal():
    # 12,300.00 - 11,500.00 = 800.00 (our suggestion did better)
    assert compare_equal_weight(make_portfolio()).difference == 800.00


@pytest.mark.unit
def test_difference_is_negative_when_equal_weight_does_better():
    # Put the most money in the worst stock: 0.1x0.40 + 0.2x0.20 + 0.3x0.10 + 0.4x(-0.10) = 0.07
    flipped = [
        ("AAA", "Technology", 0.10, 0.40),
        ("BBB", "Technology", 0.20, 0.20),
        ("CCC", "Healthcare", 0.30, 0.10),
        ("DDD", "Energy", 0.40, -0.10),
    ]
    result = compare_equal_weight(make_portfolio(stocks=flipped))
    assert result.suggested_final_value == 10_700.00
    assert result.difference == -800.00


@pytest.mark.unit
def test_difference_is_rounded_to_cents():
    result = compare_equal_weight(make_portfolio(amount=1_234.57))
    assert result.difference == round(result.difference, 2)
    assert result.difference == round(result.suggested_final_value - result.equal_final_value, 2)


@pytest.mark.unit
def test_comparison_uses_the_analysis_functions(use_contract_math):
    compare_equal_weight(make_portfolio())
    assert use_contract_math == ["portfolio_return", "final_value"]


@pytest.mark.unit
def test_decline_default_is_10_percent_of_the_amount():
    result = decline_scenario(make_portfolio(amount=10_000.00))
    assert result == Scenario(drop=0.10, base_value=10_000.00, loss=1_000.00, remaining_value=9_000.00)


@pytest.mark.unit
@pytest.mark.parametrize(
    "drop, loss, remaining",
    [
        (0.20, 2_000.00, 8_000.00),
        (0.30, 3_000.00, 7_000.00),
        (0.0, 0.00, 10_000.00),  # no drop: nothing is lost
        (1.0, 10_000.00, 0.00),  # everything is lost
    ],
)
def test_decline_works_for_any_drop(drop, loss, remaining):
    result = decline_scenario(make_portfolio(amount=10_000.00), drop=drop)
    assert result.drop == drop
    assert result.loss == loss
    assert result.remaining_value == remaining


@pytest.mark.unit
def test_decline_rounds_to_cents():
    # 1,234.56 x 0.10 = 123.456, which rounds to 123.46; 1,234.56 - 123.46 = 1,111.10
    result = decline_scenario(make_portfolio(amount=1_234.56))
    assert result.loss == 123.46
    assert result.remaining_value == 1_111.10
    assert result.loss + result.remaining_value == pytest.approx(result.base_value)


# ---------- negative: bad input gives a clear error, not a wrong answer ----------


@pytest.mark.negative
@pytest.mark.parametrize("drop", [-0.10, 1.01, 10.0, math.nan])
def test_decline_refuses_a_drop_outside_0_to_1(drop):
    with pytest.raises(ValueError, match="between 0 and 1"):
        decline_scenario(make_portfolio(), drop=drop)


@pytest.mark.negative
def test_equal_weight_refuses_a_portfolio_without_4_stocks():
    # 3 stocks at 25% each add up to 75%, not 100%.
    three = [
        ("AAA", "Technology", 0.50, 0.40),
        ("CCC", "Healthcare", 0.30, 0.10),
        ("DDD", "Energy", 0.20, -0.10),
    ]
    with pytest.raises(ValueError):
        compare_equal_weight(make_portfolio(stocks=three))


# ---------- regression: a result that must not change ----------


@pytest.mark.regression
def test_same_portfolio_gives_the_same_results():
    portfolio = make_portfolio(amount=5_432.10)
    assert compare_equal_weight(portfolio) == compare_equal_weight(portfolio)
    assert decline_scenario(portfolio) == decline_scenario(portfolio)

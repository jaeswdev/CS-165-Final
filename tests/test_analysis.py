"""Tests for src/analysis.py (task H4): returns, volatility, and portfolio math.

The unit and negative tests use small made-up numbers that are easy to check by
hand. The integration and regression tests read our real saved files in data/.
Every test has exactly one marker from pytest.ini (D21).
"""

import math

import pandas as pd
import pytest

from src.analysis import (
    TRADING_DAYS,
    allocate_dollars,
    annualized_volatility,
    compute_stock_stats,
    final_value,
    historical_return,
    load_stock_stats,
    portfolio_return,
)
from src.data_loader import Dataset

# The plan's hand-checked example: weights 40/30/20/10, returns 10%, 5%, -2%, 20%.
WEIGHTS = {"AAA": 0.40, "BBB": 0.30, "CCC": 0.20, "DDD": 0.10}
RETURNS = {"AAA": 0.10, "BBB": 0.05, "CCC": -0.02, "DDD": 0.20}


def total_cents(dollars):
    """Add up a dict of dollar amounts in whole cents, so there is no float error."""
    return sum(round(value * 100) for value in dollars.values())


def tiny_dataset():
    """3 trading days and 2 made-up stocks. The columns are NOT in A-Z order on purpose.

    ZZZ rises 10% every day: 50 -> 55 -> 60.5.
    AAA goes up 10%, then down 10%: 100 -> 110 -> 99.
    """
    dates = pd.DatetimeIndex(["2025-11-18", "2025-11-19", "2025-11-20"], name="Date")
    prices = pd.DataFrame({"ZZZ": [50.0, 55.0, 60.5], "AAA": [100.0, 110.0, 99.0]}, index=dates)
    stocks = pd.DataFrame(
        {
            "ticker": ["ZZZ", "AAA"],
            "name": ["Zed Corp.", "Aaa Inc."],
            "sector": ["Energy", "Technology"],
            "sector_source": "made-up test data",
        }
    )
    return Dataset(prices=prices, stocks=stocks)


# ---------- unit: one function on its own ----------


@pytest.mark.unit
def test_historical_return_hand_example():
    # (112 - 100) / 100 = 0.12, which is 12%
    assert historical_return(100, 112) == pytest.approx(0.12)


@pytest.mark.unit
def test_historical_return_can_be_negative():
    # (90 - 100) / 100 = -0.10: the price fell 10%
    assert historical_return(100, 90) == pytest.approx(-0.10)


@pytest.mark.unit
def test_volatility_by_hand():
    # Daily changes are +10% and -10%, and their average is 0.
    # Sample standard deviation: sqrt((0.10^2 + 0.10^2) / (2 - 1)) = 0.1414
    # Times sqrt(252) = 15.87: 2.2450
    expected = math.sqrt(0.02) * math.sqrt(TRADING_DAYS)
    assert expected == pytest.approx(2.2450, abs=1e-4)
    assert annualized_volatility(pd.Series([100.0, 110.0, 99.0])) == pytest.approx(expected)


@pytest.mark.unit
def test_volatility_is_zero_for_steady_growth():
    # +10% every day: no ups and downs, so no volatility
    assert annualized_volatility(pd.Series([100.0, 110.0, 121.0])) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.unit
def test_portfolio_return_hand_example():
    # 0.4 x 0.10 + 0.3 x 0.05 + 0.2 x (-0.02) + 0.1 x 0.20 = 0.071 (7.1%).
    # A computer gives 0.07100000000000001, so we compare with pytest.approx, not ==.
    assert portfolio_return(WEIGHTS, RETURNS) == pytest.approx(0.071)


@pytest.mark.unit
def test_portfolio_return_does_not_depend_on_ticker_order():
    reversed_weights = dict(reversed(list(WEIGHTS.items())))
    assert portfolio_return(reversed_weights, RETURNS) == portfolio_return(WEIGHTS, RETURNS)


@pytest.mark.unit
def test_portfolio_return_ignores_stocks_that_are_not_chosen():
    # Like our 15-stock table: EEE has a return but no weight, so it does not count.
    all_returns = {**RETURNS, "EEE": 9.99}
    assert portfolio_return(WEIGHTS, all_returns) == pytest.approx(0.071)


@pytest.mark.unit
def test_weights_just_inside_the_tolerance_are_accepted():
    # Boundary value (Lecture 22, slide 15): 0.0000005 over 1 is inside the 1e-6 tolerance.
    weights = {**WEIGHTS, "DDD": 0.10 + 5e-7}
    assert portfolio_return(weights, RETURNS) == pytest.approx(0.071, abs=1e-6)


@pytest.mark.unit
def test_final_value_hand_example():
    # $10,000 x (1 + 0.071) = $10,710.00
    assert final_value(10_000, 0.071) == 10_710.00


@pytest.mark.unit
def test_final_value_rounds_to_cents():
    # $1,234.56 x 1.10 = $1,358.016, which rounds to $1,358.02
    assert final_value(1_234.56, 0.10) == 1_358.02


@pytest.mark.unit
def test_allocate_even_split():
    weights = {"AAA": 0.30, "BBB": 0.30, "CCC": 0.20, "DDD": 0.20}
    assert allocate_dollars(weights, 1_000.00) == {
        "AAA": 300.00,
        "BBB": 300.00,
        "CCC": 200.00,
        "DDD": 200.00,
    }


@pytest.mark.unit
def test_allocate_gives_leftover_cents_to_the_largest_weight():
    # $999.99 = 99,999 cents. Floors: 29,999 + 29,999 + 19,999 + 19,999 = 99,996.
    # The 3 leftover cents go to the largest weight. AAA and BBB tie, so AAA (first A-Z) gets them.
    weights = {"AAA": 0.30, "BBB": 0.30, "CCC": 0.20, "DDD": 0.20}
    dollars = allocate_dollars(weights, 999.99)
    assert dollars == {"AAA": 300.02, "BBB": 299.99, "CCC": 199.99, "DDD": 199.99}
    assert total_cents(dollars) == 99_999  # exactly $999.99


@pytest.mark.unit
def test_allocate_tie_goes_to_the_first_ticker_a_to_z():
    # The same split, but the dict is not in A-Z order: AAA still gets the 3 leftover cents.
    weights = {"BBB": 0.30, "DDD": 0.20, "AAA": 0.30, "CCC": 0.20}
    assert allocate_dollars(weights, 999.99)["AAA"] == 300.02


@pytest.mark.unit
def test_allocate_does_not_lose_a_cent_when_converting_to_cents():
    # 4.35 x 100 = 434.99999999999994 in a computer, and int() would make it 434 cents.
    # 435 cents: floors 174 + 130 + 87 + 43 = 434, and the 1 leftover cent goes to AAA (40%).
    dollars = allocate_dollars(WEIGHTS, 4.35)
    assert dollars == {"AAA": 1.75, "BBB": 1.30, "CCC": 0.87, "DDD": 0.43}
    assert total_cents(dollars) == 435


@pytest.mark.unit
def test_allocate_exact_split_is_not_off_by_a_cent():
    # 0.29 x 100,000 = 28,999.999999999996 in a computer, so a plain floor would give 28,999.
    weights = {"AAA": 0.29, "BBB": 0.29, "CCC": 0.21, "DDD": 0.21}
    assert allocate_dollars(weights, 1_000.00) == {
        "AAA": 290.00,
        "BBB": 290.00,
        "CCC": 210.00,
        "DDD": 210.00,
    }


@pytest.mark.unit
@pytest.mark.parametrize("amount", [1.00, 1.03, 4.35, 999.99, 1_234.57, 10_000_000.00])
def test_allocate_always_adds_up_to_the_amount(amount):
    # The invariant (Lecture 22, slide 18), from the $1.00 minimum to the $10,000,000 maximum.
    weights = {"AAA": 0.35, "BBB": 0.25, "CCC": 0.25, "DDD": 0.15}
    assert total_cents(allocate_dollars(weights, amount)) == round(amount * 100)


@pytest.mark.unit
def test_compute_stock_stats_on_a_tiny_dataset():
    stats = compute_stock_stats(tiny_dataset())
    assert [s.ticker for s in stats] == ["AAA", "ZZZ"]  # sorted A-Z, not in column order
    aaa, zzz = stats
    assert (aaa.name, aaa.sector) == ("Aaa Inc.", "Technology")
    assert (aaa.start_date, aaa.end_date) == ("2025-11-18", "2025-11-20")
    assert (aaa.start_price, aaa.end_price) == (100.0, 99.0)
    assert aaa.hist_return == pytest.approx(-0.01)  # (99 - 100) / 100
    assert aaa.volatility == pytest.approx(2.2450, abs=1e-4)  # +10%, then -10%
    assert (zzz.name, zzz.sector) == ("Zed Corp.", "Energy")
    assert zzz.hist_return == pytest.approx(0.21)  # (60.5 - 50) / 50
    assert zzz.volatility == pytest.approx(0.0, abs=1e-12)  # +10% every day: no ups and downs


# ---------- negative: bad input gives a clear error, not a wrong answer ----------


@pytest.mark.negative
@pytest.mark.parametrize("start_price", [0, -5.0, math.nan], ids=["zero", "negative", "nan"])
def test_historical_return_refuses_a_bad_start_price(start_price):
    with pytest.raises(ValueError, match="start price"):
        historical_return(start_price, 112)


@pytest.mark.negative
@pytest.mark.parametrize("change", [-0.10, 2e-6], ids=["adds-up-to-0.9", "just-over-the-tolerance"])
def test_portfolio_return_refuses_weights_that_do_not_add_up_to_1(change):
    weights = {**WEIGHTS, "DDD": 0.10 + change}
    with pytest.raises(ValueError, match="add up to 1"):
        portfolio_return(weights, RETURNS)


@pytest.mark.negative
def test_portfolio_return_refuses_a_ticker_without_a_return():
    with pytest.raises(ValueError, match="No return for DDD"):
        portfolio_return(WEIGHTS, {"AAA": 0.10, "BBB": 0.05, "CCC": -0.02})


@pytest.mark.negative
def test_allocate_refuses_weights_that_do_not_add_up_to_1():
    with pytest.raises(ValueError, match="add up to 1"):
        allocate_dollars({"AAA": 0.50, "BBB": 0.30}, 1_000.00)


@pytest.mark.negative
@pytest.mark.parametrize(
    "prices",
    [[100.0], [100.0, 0.0, 99.0], [100.0, math.nan, 99.0]],
    ids=["one-price", "zero", "nan"],
)
def test_volatility_refuses_bad_prices(prices):
    with pytest.raises(ValueError):
        annualized_volatility(pd.Series(prices))


@pytest.mark.negative
def test_compute_stock_stats_refuses_an_empty_prices_table():
    data = tiny_dataset()
    with pytest.raises(ValueError, match="empty"):
        compute_stock_stats(Dataset(prices=data.prices.iloc[0:0], stocks=data.stocks))


@pytest.mark.negative
def test_compute_stock_stats_refuses_a_ticker_without_facts():
    data = tiny_dataset()
    without_zzz = Dataset(prices=data.prices, stocks=data.stocks[data.stocks["ticker"] != "ZZZ"])
    with pytest.raises(ValueError, match="ZZZ"):
        compute_stock_stats(without_zzz)


# ---------- integration: data_loader.py and analysis.py together, on our real data ----------


@pytest.mark.integration
def test_load_stock_stats_on_our_real_data():
    stats = load_stock_stats()
    assert len(stats) == 15
    assert len({s.sector for s in stats}) == 3
    assert [s.ticker for s in stats] == sorted(s.ticker for s in stats)
    assert all(-1 <= s.hist_return <= 5 for s in stats)
    assert all(s.volatility > 0 for s in stats)
    assert {(s.start_date, s.end_date) for s in stats} == {("2025-11-18", "2026-11-18")}


# ---------- regression: a result that must not change ----------


@pytest.mark.regression
def test_aapl_result_on_our_saved_data_does_not_change():
    # Pinned on Nov 27, 2026 from the snapshot in data/ (downloaded Nov 24, 2026).
    aapl = next(s for s in load_stock_stats() if s.ticker == "AAPL")
    assert aapl.start_price == 266.5115051269531
    assert aapl.end_price == 352.45001220703125
    assert aapl.hist_return == pytest.approx(0.32245702503215085, rel=1e-12)
    assert aapl.volatility == pytest.approx(0.24881708437776612, rel=1e-12)

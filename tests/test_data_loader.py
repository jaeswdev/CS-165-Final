"""Tests for src/data_loader.py (task H3): the cleaning, the providers, and the DataError checks.

The unit and negative tests write small made-up CSV files into a temporary folder
(pytest's tmp_path), so they never use the internet. The integration and regression
tests read our real saved files in data/.
Every test has exactly one marker from pytest.ini (D21).
"""

import sys
import types

import numpy as np
import pandas as pd
import pytest

from src.data_loader import (
    CsvProvider,
    DataError,
    PriceProvider,
    YahooFinanceProvider,
    load_dataset,
)

# Four made-up stocks in 3 sectors, and more days than the 200-day minimum.
SECTORS = {"AAA": "Technology", "BBB": "Technology", "CCC": "Healthcare", "DDD": "Energy"}
DAYS = 220


def make_tables(sectors=SECTORS, days=DAYS):
    """Build valid made-up tables. Each price rises by $1 a day, so it is easy to check."""
    dates = pd.bdate_range("2025-01-02", periods=days).strftime("%Y-%m-%d")
    prices = pd.DataFrame(
        {ticker: 100.0 + 10 * i + np.arange(days) for i, ticker in enumerate(sectors)},
        index=pd.Index(dates, name="Date"),
    ).astype(object)  # object, so a test can put text such as "abc" into a cell
    stocks = pd.DataFrame(
        {
            "ticker": list(sectors),
            "name": [f"{ticker} Inc." for ticker in sectors],
            "sector": list(sectors.values()),
            "sector_source": "made-up test data",
        }
    )
    return prices, stocks


def load_from(folder, prices, stocks):
    """Save the tables as prices.csv and stocks.csv (like the download script), then load them."""
    prices.to_csv(folder / "prices.csv")
    stocks.to_csv(folder / "stocks.csv", index=False)
    return CsvProvider(folder).load()


# ---------- unit: one function or class on its own ----------


@pytest.mark.unit
def test_clean_data_loads_unchanged(tmp_path):
    prices, stocks = make_tables()
    data = load_from(tmp_path, prices, stocks)
    assert data.prices.shape == (DAYS, 4)
    assert data.prices.index.name == "Date"
    assert data.prices.index.is_monotonic_increasing
    assert not data.prices.isna().any().any()
    assert data.prices.iloc[0].tolist() == [100.0, 110.0, 120.0, 130.0]
    assert data.stocks["ticker"].tolist() == list(data.prices.columns)


@pytest.mark.unit
def test_one_day_gap_is_filled_with_the_day_before(tmp_path):
    prices, stocks = make_tables()
    prices.iloc[10, 0] = ""  # AAA has no price on day 10
    data = load_from(tmp_path, prices, stocks)
    assert data.prices["AAA"].iloc[10] == data.prices["AAA"].iloc[9] == 109.0
    assert len(data.prices) == DAYS


@pytest.mark.unit
def test_two_day_gap_is_filled_but_three_day_gap_is_not(tmp_path):
    prices, stocks = make_tables()
    prices.iloc[60:62, 1] = ""  # BBB: 2 days missing -> filled
    prices.iloc[100:103, 1] = ""  # BBB: 3 days missing -> not filled, so those days are dropped
    data = load_from(tmp_path, prices, stocks)
    assert data.prices["BBB"].iloc[61] == data.prices["BBB"].iloc[59]
    assert len(data.prices) == DAYS - 3
    assert not data.prices.isna().any().any()


@pytest.mark.unit
def test_ticker_with_too_many_gaps_is_dropped(tmp_path):
    sectors = dict(SECTORS, EEE="Energy")  # a 2nd Energy stock, so 3 sectors stay after the drop
    prices, stocks = make_tables(sectors)
    prices.iloc[50:70, 4] = ""  # EEE misses 20 of 220 days (9%, more than 5%)
    with pytest.warns(UserWarning, match="Dropped EEE"):
        data = load_from(tmp_path, prices, stocks)
    assert "EEE" not in data.prices.columns
    assert "EEE" not in data.stocks["ticker"].tolist()
    assert len(data.prices) == DAYS


@pytest.mark.unit
def test_day_with_no_prices_is_dropped(tmp_path):
    prices, stocks = make_tables()
    prices.iloc[5, :] = ""  # no stock has a price on day 5 (like a holiday row)
    data = load_from(tmp_path, prices, stocks)
    assert len(data.prices) == DAYS - 1


@pytest.mark.unit
def test_dates_are_sorted_oldest_first(tmp_path):
    prices, stocks = make_tables()
    data = load_from(tmp_path, prices.iloc[::-1], stocks)  # saved newest first
    assert data.prices.index.is_monotonic_increasing


@pytest.mark.unit
def test_price_provider_is_only_an_interface():
    with pytest.raises(TypeError):
        PriceProvider()


@pytest.mark.unit
def test_yahoo_provider_uses_the_same_cleaning(monkeypatch):
    # A fake yfinance (a "test double", Lecture 22 slide 10), so this test needs no internet.
    prices, stocks = make_tables()
    prices.iloc[10, 0] = 0  # a bad price, to show that the same cleaning runs
    columns = pd.MultiIndex.from_product([["Close"], list(SECTORS)], names=["Price", "Ticker"])
    raw = pd.DataFrame(
        prices.to_numpy(dtype=float), index=pd.to_datetime(prices.index), columns=columns
    )
    fake = types.ModuleType("yfinance")
    fake.download = lambda *args, **kwargs: raw
    fake.Ticker = lambda ticker: types.SimpleNamespace(
        info={"longName": f"{ticker} Inc.", "sector": SECTORS[ticker]}
    )
    monkeypatch.setitem(sys.modules, "yfinance", fake)

    data = YahooFinanceProvider(list(SECTORS), "2025-01-02", "2025-11-12").load()
    assert data.prices.shape == (DAYS, 4)
    assert data.prices["AAA"].iloc[10] == data.prices["AAA"].iloc[9]
    assert data.stocks["sector"].tolist() == list(SECTORS.values())


# ---------- negative: bad data gives a clear error or is cleaned, never a wrong answer ----------


@pytest.mark.negative
@pytest.mark.parametrize("bad_price", [0, -5, "abc", ""], ids=["zero", "negative", "text", "blank"])
def test_bad_price_counts_as_missing(tmp_path, bad_price):
    prices, stocks = make_tables()
    prices.iloc[10, 0] = bad_price
    data = load_from(tmp_path, prices, stocks)
    # The bad price is gone: the 1-day gap is filled with the day before.
    assert data.prices["AAA"].iloc[10] == data.prices["AAA"].iloc[9] == 109.0


@pytest.mark.negative
def test_missing_file_raises_data_error(tmp_path):
    with pytest.raises(DataError, match="Missing data file"):
        CsvProvider(tmp_path).load()  # tmp_path is an empty folder


@pytest.mark.negative
def test_only_two_sectors_raises_data_error(tmp_path):
    prices, stocks = make_tables({"AAA": "Technology", "BBB": "Technology", "CCC": "Healthcare"})
    with pytest.raises(DataError, match="at least 3"):
        load_from(tmp_path, prices, stocks)


@pytest.mark.negative
def test_fewer_than_200_days_raises_data_error(tmp_path):
    prices, stocks = make_tables(days=150)
    with pytest.raises(DataError, match="at least 200"):
        load_from(tmp_path, prices, stocks)


@pytest.mark.negative
def test_more_than_20_tickers_raises_data_error(tmp_path):
    sectors = {f"T{i:02d}": ["Technology", "Healthcare", "Energy"][i % 3] for i in range(21)}
    prices, stocks = make_tables(sectors)
    with pytest.raises(DataError, match="at most 20"):
        load_from(tmp_path, prices, stocks)


@pytest.mark.negative
def test_ticker_without_a_stocks_row_raises_data_error(tmp_path):
    prices, stocks = make_tables()
    with pytest.raises(DataError, match="no name or sector for AAA"):
        load_from(tmp_path, prices, stocks.iloc[1:])  # the AAA row is missing


@pytest.mark.negative
def test_bad_date_raises_data_error(tmp_path):
    prices, stocks = make_tables()
    prices.index = pd.Index([*prices.index[:-1], "2025-13-45"], name="Date")  # month 13
    with pytest.raises(DataError, match="YYYY-MM-DD"):
        load_from(tmp_path, prices, stocks)


# ---------- integration: our real data files with the cleaning ----------


@pytest.mark.integration
def test_real_data_files_load():
    data = load_dataset()
    assert len(data.prices.columns) == 15
    assert data.stocks["sector"].nunique() == 3
    assert len(data.prices) >= 200
    assert str(data.prices.index[0].date()) == "2025-11-18"
    assert str(data.prices.index[-1].date()) == "2026-11-18"
    assert not data.prices.isna().any().any()
    assert data.stocks["ticker"].tolist() == list(data.prices.columns)


@pytest.mark.integration
def test_loading_twice_gives_exactly_the_same_data():
    first, second = load_dataset(), load_dataset()
    pd.testing.assert_frame_equal(first.prices, second.prices)
    pd.testing.assert_frame_equal(first.stocks, second.stocks)


# ---------- regression: a result that must not change ----------


@pytest.mark.regression
def test_saved_snapshot_does_not_change():
    # Our numbers must stay the same for testing and grading (D2). If this fails,
    # someone downloaded the data again: check data/README.md before you continue.
    data = load_dataset()
    assert len(data.prices) == 252
    assert data.prices["AAPL"].iloc[0] == 266.5115051269531  # full decimals, never rounded

# Data: one year of prices for 15 stocks

This folder holds the saved data that the app uses. The app never downloads anything. It reads these two files (decision D2), so it works offline and gives the same numbers every time, for our tests and for grading.

| File | What it holds |
|---|---|
| `prices.csv` | Daily prices: one row per trading day (`Date`, YYYY-MM-DD, oldest first) and one column per ticker with that day's **adjusted close** price, with full decimals. |
| `stocks.csv` | Company facts that rarely change: one row per stock, with `ticker`, `name`, `sector`, and `sector_source`. |

Both files are **raw**: they hold exactly what Yahoo returned. The cleaning happens when the app loads them (see [Cleaning steps](#cleaning-steps)).

## Source

- **Yahoo Finance**, through the **yfinance** Python library, version 1.8.0 (pinned in `requirements.txt`). yfinance is free and open source. It is not made by Yahoo, and it is meant for research and educational use.
- **Adjusted close:** the download uses `auto_adjust=True`, so each Close price is adjusted for stock splits and dividends.
- **Sector labels** come from the same source, yfinance `Ticker.info["sector"]`. The `sector_source` column records this for every stock.
- **Company names** come from yfinance `Ticker.info["longName"]`, exactly as Yahoo writes them.

## Download details

| Item | Value |
|---|---|
| Downloaded on | Tuesday, November 24, 2026, by Henry, with `scripts/download_data.py` |
| Window | November 18, 2025 to November 18, 2026 (both days included) |
| Trading days | 252 |
| Missing prices in the download | 0 for every ticker |
| Tickers dropped by the cleaning | None |

The script asks yfinance for `end="2026-11-19"`, because yfinance does not include the end date itself.

## Tickers and sectors (15 stocks, 3 sectors)

| Sector | Ticker | Company (as Yahoo names it) |
|---|---|---|
| Technology | AAPL | Apple Inc. |
| Technology | MSFT | Microsoft Corporation |
| Technology | NVDA | NVIDIA Corporation |
| Technology | ORCL | Oracle Corporation |
| Technology | CSCO | Cisco Systems, Inc. |
| Healthcare | JNJ | Johnson & Johnson |
| Healthcare | UNH | UnitedHealth Group Incorporated |
| Healthcare | PFE | Pfizer Inc. |
| Healthcare | MRK | Merck & Co., Inc. |
| Healthcare | ABBV | AbbVie Inc. |
| Energy | XOM | ExxonMobil Holdings Corporation |
| Energy | CVX | Chevron Corporation |
| Energy | COP | ConocoPhillips |
| Energy | SLB | SLB N.V. |
| Energy | EOG | EOG Resources, Inc. |

## Cleaning steps

`src/data_loader.py` cleans the data every time it is loaded. One function, `clean_dataset`, does the cleaning for both data providers, `CsvProvider` and `YahooFinanceProvider` (decisions D18 and D19). The saved files are never changed. The steps, in this order:

1. **Bad prices count as missing:** a price that is blank, text (like "abc"), zero, negative, or infinite.
2. **Drop the days where every price is missing**, such as an empty row.
3. **Fill short gaps:** a gap of at most 2 trading days gets the last known price (forward-fill). Longer gaps are not filled.
4. **Drop a ticker that is still missing more than 5% of the days**, with a warning. A dropped ticker must be listed in [Download details](#download-details). So far, none.
5. **Drop the days where a remaining stock still has no price**, so every stock has a price on every day. `CONTRACT.md` promises no missing values after cleaning, and this step keeps that promise when a gap is longer than 2 days.

Prices are never rounded: the calculations use the full decimals.

After cleaning, the loader checks the rules. It raises `DataError` with a clear message if a data file is missing or cannot be read, if there are more than 20 tickers (section 3), fewer than 3 sectors, or fewer than 200 trading days, if a ticker has no row in `stocks.csv`, or if a date is not YYYY-MM-DD.

With the November 24 download, the cleaning changes nothing, because no price is missing or bad.

## How to download again

From the project folder, with the virtual environment on:

```
python scripts/download_data.py
```

The script downloads the same 15 tickers for the same window. It checks every sector label and stops if Yahoo changed one, so we can swap that ticker (decision D4). It tries up to 3 times if Yahoo blocks or slows us down. Then it saves both files and prints the number of days and the missing prices per ticker. After it finishes, run `pytest`.

A new download will not give exactly the same numbers. When a company pays a dividend or splits its stock, Yahoo adjusts all of its older prices again. The test `test_saved_snapshot_does_not_change` fails on purpose when the numbers change. Download again only when the team agrees, and then update this file and that test.

## If Yahoo corrects an old price

Yahoo sometimes fixes a wrong price later. We would not replace the whole file, because a full new download also changes the other days (see above), and every result would change. Instead:

1. Note the ticker and the day that Yahoo corrected.
2. Download that ticker again and compare its prices with ours, to see which days changed.
3. In `prices.csv`, replace only the prices of the corrected days.
4. Add a row to [Changes](#changes), run `pytest`, and tell the team, because results in the app and the report may change.

## If our saved data gets old

The data ends on November 18, 2026, and it does not update by itself. This is on purpose (D2): everyone, including the graders, sees the same numbers. To use a newer year, change `START` and `END` in `scripts/download_data.py`, download again, and then update this file, the regression test, and the dates in the report.

## Changes

| Date | Ticker | Day | What changed | Why |
|---|---|---|---|---|
| None yet | | | No changes since the November 24, 2026 download | |

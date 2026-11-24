"""Download one year of prices for our 15 stocks and save them in data/ (task H3).

Run it from the project folder:  python scripts/download_data.py
The app never downloads anything. It only reads the saved files (decision D2).
"""

import sys
import time
from pathlib import Path

# Lets this script import src/ when you run "python scripts/download_data.py".
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import DATA_DIR, YahooFinanceProvider

# Our 15 stocks and the sector we expect Yahoo to give each one (CONTRACT.md, D4).
EXPECTED_SECTORS = {
    "AAPL": "Technology", "MSFT": "Technology", "NVDA": "Technology",
    "ORCL": "Technology", "CSCO": "Technology",
    "JNJ": "Healthcare", "UNH": "Healthcare", "PFE": "Healthcare",
    "MRK": "Healthcare", "ABBV": "Healthcare",
    "XOM": "Energy", "CVX": "Energy", "COP": "Energy", "SLB": "Energy", "EOG": "Energy",
}
TICKERS = list(EXPECTED_SECTORS)
START = "2025-11-18"
END = "2026-11-19"  # yfinance does not include the end date, so the last day is Nov 18, 2026
TRIES = 3
WAIT_SECONDS = 60


def download():
    """Get the raw tables from Yahoo. Try again if Yahoo blocks or slows us down."""
    provider = YahooFinanceProvider(TICKERS, START, END)
    for attempt in range(1, TRIES + 1):
        try:
            prices, stocks = provider.fetch()
            failed = [t for t in TICKERS if prices[t].isna().all()]
            if not failed:
                return prices, stocks
            print(f"No prices came back for {failed}.")
        except Exception as error:  # Yahoo can fail in many ways, so we catch them all here
            print(f"Download failed: {error}")
        if attempt < TRIES:
            print(f"Waiting {WAIT_SECONDS} seconds, then trying again ({attempt + 1} of {TRIES})...")
            time.sleep(WAIT_SECONDS)
    sys.exit("Stop: the download failed 3 times. Wait a few minutes and run the script again.")


def main():
    prices, stocks = download()

    # Check every sector label before saving anything (D4).
    for row in stocks.itertuples():
        expected = EXPECTED_SECTORS[row.ticker]
        if row.sector != expected:
            sys.exit(
                f"Stop: Yahoo says {row.ticker} is in '{row.sector}', but we expected "
                f"'{expected}'. Swap this ticker for another {expected} stock (D4)."
            )

    # Save the raw tables. The cleaning happens later, when the app loads them.
    DATA_DIR.mkdir(exist_ok=True)
    prices.to_csv(DATA_DIR / "prices.csv")
    stocks.to_csv(DATA_DIR / "stocks.csv", index=False)

    print(
        f"Saved data/prices.csv: {len(prices)} trading days, "
        f"{prices.index[0].date()} to {prices.index[-1].date()}"
    )
    print(f"Saved data/stocks.csv: {len(stocks)} stocks in {stocks['sector'].nunique()} sectors")
    print("Missing prices per ticker:")
    print(prices.isna().sum().to_string())


if __name__ == "__main__":
    main()

# CONTRACT.md: shared interfaces for our Stock Portfolio Suggestion Engine
Change this file only after telling the team, and only with a yes from every module owner it affects.
Last change: Nov 24 (D18 bad prices, D19 price providers, D21 test markers, the drop check in decline_scenario).

## Architecture and rules
- Layered: app.py (presentation) -> src/validation.py, src/analysis.py, src/strategy.py, src/comparison.py (logic) -> src/data_loader.py (data) -> data/*.csv
- Only app.py imports streamlit. Only src/analysis.py calls src/data_loader.py. Calls go down, never up.
- Logic functions are pure: no file reads, printing, or network (the one exception is analysis.load_stock_stats).
- The app never calls an AI API. No AI library in requirements.txt.
- Units: returns, weights, volatility, and drop are fractions (0.1234 means 12.34%). Money is a float in dollars, rounded to cents.
- Tests: each test has exactly one marker from pytest.ini (unit, integration, acceptance, negative, or regression); pytest runs with --strict-markers.

## Data files (raw, made by scripts/download_data.py, committed to the repo; the cleaning happens when they are loaded)
- data/prices.csv: column Date (YYYY-MM-DD, oldest first), then one column per ticker with the adjusted close (yfinance, auto_adjust=True). Window: 2025-11-18 to 2026-11-18.
- data/stocks.csv: columns ticker, name, sector, sector_source. sector comes from yfinance Ticker.info["sector"].
- data/README.md: source, download date, window, tickers, cleaning steps, how to download again, and how we would handle a price that Yahoo corrects later.
- Tickers: Technology AAPL, MSFT, NVDA, ORCL, CSCO; Healthcare JNJ, UNH, PFE, MRK, ABBV; Energy XOM, CVX, COP, SLB, EOG.

## src/models.py (shared data classes, all @dataclass(frozen=True))
- StockStats: ticker: str, name: str, sector: str, start_date: str, end_date: str, start_price: float, end_price: float, hist_return: float, volatility: float
- Holding: ticker: str, name: str, sector: str, weight: float, dollars: float, hist_return: float
- Portfolio: profile: str, amount: float, holdings: tuple[Holding, ...] (exactly 4), portfolio_return: float, final_value: float, why_selected: str, profile_effect: str
- Comparison: suggested_return: float, suggested_final_value: float, equal_return: float, equal_final_value: float, difference: float
- Scenario: drop: float, base_value: float, loss: float, remaining_value: float

## src/data_loader.py (data layer, owner Henry)
- DATA_DIR: Path to the repository's data/ folder
- class DataError(Exception)
- @dataclass(frozen=True, eq=False) Dataset: prices: pd.DataFrame, stocks: pd.DataFrame
- class PriceProvider(ABC): load() -> Dataset (D19)
- CsvProvider(data_dir: Path = DATA_DIR): load() reads data/prices.csv and data/stocks.csv, then cleans and checks them. The app uses only this provider.
- YahooFinanceProvider(tickers: list[str], start: str, end: str): fetch() -> tuple[pd.DataFrame, pd.DataFrame] downloads the raw prices and stocks tables (yfinance is imported inside fetch); load() cleans and checks what fetch() returns. Only scripts/download_data.py uses it.
- load_dataset(data_dir: Path = DATA_DIR) -> Dataset: returns CsvProvider(data_dir).load()
  - prices: DatetimeIndex named "Date", oldest first, one float column per ticker, no missing values after cleaning
  - stocks: columns ticker, name, sector, sector_source; the same tickers as prices
  - Cleaning (one function that both providers use): first treat a price that is blank, text, zero, or negative as missing (D18); then drop days where every price is missing; forward-fill a gap of at most 2 trading days; drop a ticker missing more than 5% of days (and note it in data/README.md)
  - Raise DataError with a clear message if a file is missing, or there are more than 20 tickers, fewer than 3 sectors, or fewer than 200 trading days

## src/analysis.py (logic, owner Henry)
- TRADING_DAYS = 252
- historical_return(start_price: float, end_price: float) -> float: (end - start) / start; ValueError if start_price <= 0
- annualized_volatility(prices: pd.Series) -> float: standard deviation of daily percent changes x sqrt(252)
- compute_stock_stats(dataset: Dataset) -> list[StockStats]: one per ticker, sorted by ticker; start = first row, end = last row
- load_stock_stats(data_dir: Path = DATA_DIR) -> list[StockStats]: load_dataset, then compute_stock_stats
- portfolio_return(weights: dict[str, float], returns: dict[str, float]) -> float: sum of weight x return; ValueError if the weights do not sum to 1 (within 1e-6) or a ticker has no return
- final_value(amount: float, port_return: float) -> float: round(amount x (1 + port_return), 2)
- allocate_dollars(weights: dict[str, float], amount: float) -> dict[str, float]: work in whole cents; each ticker gets floor(weight x total cents); the leftover cents (at most 3) go to the largest weight (tie: first ticker A-Z); the total equals the amount exactly

## src/validation.py (logic, owner Anahi)
- PROFILES = ("Conservative", "Balanced", "Growth"); MIN_AMOUNT = 1.00; MAX_AMOUNT = 10_000_000.00
- parse_amount(text: str | None) -> tuple[float | None, str | None]: (amount, None) if valid, else (None, message)
- validate_profile(value: str | None) -> tuple[str | None, str | None]: (profile, None) or (None, message)
- Accepted format: trim spaces; allow one leading "$" and commas ("$1,000.50"); then only digits with at most one decimal point
- Check in this order, with exactly these messages:
  1. blank or only spaces: "Please enter an investment amount."
  2. a minus sign before the number ("-50", "$-50"): "The amount must be more than $0."
  3. not a number ("abc", "12a", "1.2.3", "1e5", "nan"): "Please enter a number, like 1000 or 1,000.50."
  4. more than 2 decimal places: "Please use at most 2 decimal places."
  5. 0 or less than 1.00: "The amount must be at least $1.00."
  6. more than 10,000,000: "Please enter $10,000,000 or less."
  7. profile missing or not in PROFILES: "Please choose Conservative, Balanced, or Growth."

## src/strategy.py (logic, Strategy design pattern, owner Chelsea)
- class ProfileStrategy(ABC): name: str; select(stats: list[StockStats]) -> dict[str, float] (ticker -> weight); explain(stats: list[StockStats], weights: dict[str, float]) -> tuple[str, str] (why_selected, profile_effect)
- ConservativeStrategy, BalancedStrategy, GrowthStrategy: one class per profile
- STRATEGIES: dict[str, ProfileStrategy], for example "Conservative" -> ConservativeStrategy()
- suggest_portfolio(profile: str, stats: list[StockStats], amount: float) -> Portfolio: picks the strategy, gets the weights, then uses analysis.allocate_dollars, analysis.portfolio_return, and analysis.final_value
- check_rules(portfolio: Portfolio) -> list[str]: the broken rules; an empty list means every rule passes
- Hard rules: exactly 4 different tickers; at least 3 sectors; every weight > 0; weights sum to 1 (within 1e-6); dollars sum to the amount exactly; the same input always gives the same output; ties broken by ticker A-Z; the 3 profiles give different portfolios on our data; at least 2 profiles use unequal weights; only the saved data is used, never live data or AI

## src/comparison.py (logic, owner Chelsea)
- compare_equal_weight(portfolio: Portfolio) -> Comparison: the same 4 tickers at 25% each; difference = suggested_final_value - equal_final_value; uses the analysis functions
- decline_scenario(portfolio: Portfolio, drop: float = 0.10) -> Scenario: base_value = portfolio.amount; loss = round(base_value x drop, 2); remaining_value = round(base_value - loss, 2); ValueError if drop < 0 or drop > 1. The drop is a parameter, so 20% or 30% needs no new code.

## app.py (presentation, owner Anahi)
- Calls only: validation.parse_amount, validation.validate_profile, analysis.load_stock_stats (inside @st.cache_data), strategy.suggest_portfolio, comparison.compare_equal_weight, comparison.decline_scenario
- Shows, top to bottom: title and purpose; "Educational only" notice; amount box (st.text_input) and profile select box (options from validation.PROFILES, no default); a button; error messages; stock analysis table for all stocks (ticker, company, sector, historical return; the chosen 4 marked); suggestion table (ticker, company, sector, weight %, dollars, historical return, and a total row); portfolio return and estimated final value; "Why these stocks"; "How your risk profile changed this"; the equal-weight comparison; "If all 4 stocks fall 10%"; the data source and period
- Formats: percents with 2 decimals ("12.34%"); dollars with commas and cents ("$1,234.56")

## Git
- One branch per task: name/TaskID-short-name, for example henry/H3-data
- Pull request into main; 1 approval; all tests pass before merging

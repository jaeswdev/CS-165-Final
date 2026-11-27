"""Logic layer: the equal-weight comparison and the -10% scenario (owner: Chelsea).

See the src/comparison.py section of CONTRACT.md and Decisions D10 and D11.
Both functions are pure: they only use the Portfolio they are given, and the
math comes from src/analysis.py so there is one formula for each thing.
"""

from src import analysis  # reuse portfolio_return and final_value instead of new formulas
from src.models import Comparison, Portfolio, Scenario

EQUAL_WEIGHT = 0.25  # D10: the same 4 stocks at 25% each


def compare_equal_weight(portfolio: Portfolio) -> Comparison:
    """Compare portfolio with the same 4 stocks at 25% each (assumption D10).

    difference = suggested_final_value - equal_final_value, rounded to cents.
    A positive difference means our suggestion did better than equal weights.
    """
    returns = {holding.ticker: holding.hist_return for holding in portfolio.holdings}
    equal_weights = {ticker: EQUAL_WEIGHT for ticker in returns}

    # portfolio_return raises ValueError if the weights do not add up to 1,
    # so a portfolio without exactly 4 different stocks is refused here.
    equal_return = analysis.portfolio_return(equal_weights, returns)
    equal_final_value = analysis.final_value(portfolio.amount, equal_return)

    return Comparison(
        suggested_return=portfolio.portfolio_return,
        suggested_final_value=portfolio.final_value,
        equal_return=equal_return,
        equal_final_value=equal_final_value,
        difference=round(portfolio.final_value - equal_final_value, 2),
    )


def decline_scenario(portfolio: Portfolio, drop: float = 0.10) -> Scenario:
    """Show what happens if every chosen stock falls by drop (assumption D11).

    The drop applies to the amount invested:
    loss = round(amount x drop, 2) and remaining_value = round(amount - loss, 2).
    drop is a fraction (0.10 means 10%), so 20% or 30% needs no new code.
    Raises ValueError if drop is below 0 or above 1.
    """
    # "not (0 <= drop <= 1)" also catches nan, which "drop < 0 or drop > 1" would let through.
    if not 0 <= drop <= 1:
        raise ValueError(f"drop must be between 0 and 1 (0.10 means 10%), got {drop}")

    base_value = portfolio.amount
    loss = round(base_value * drop, 2)
    return Scenario(
        drop=drop,
        base_value=base_value,
        loss=loss,
        remaining_value=round(base_value - loss, 2),
    )

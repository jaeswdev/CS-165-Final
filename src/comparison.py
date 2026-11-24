"""Logic layer: the equal-weight comparison and the -10% scenario (owner: Chelsea).

See the src/comparison.py section of CONTRACT.md and Decisions D10 and D11.
This is a stub: the names and types are final; the code comes in task C3.
"""

from src import analysis  # reuse portfolio_return and final_value instead of new formulas (C3)
from src.models import Comparison, Portfolio, Scenario


def compare_equal_weight(portfolio: Portfolio) -> Comparison:
    """Compare portfolio with the same 4 stocks at 25% each (assumption D10).

    difference = suggested_final_value - equal_final_value.
    """
    raise NotImplementedError("C3 (Chelsea): due Wed 11/25, 6:00 PM")


def decline_scenario(portfolio: Portfolio, drop: float = 0.10) -> Scenario:
    """Show what happens if every chosen stock falls by drop (assumption D11).

    The drop applies to the amount invested:
    loss = round(amount x drop, 2) and remaining_value = round(amount - loss, 2).
    """
    raise NotImplementedError("C3 (Chelsea): due Wed 11/25, 6:00 PM")

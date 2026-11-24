"""Logic layer: risk-profile strategies, using the Strategy design pattern (owner: Chelsea).

Each risk profile is one class with the same two methods (select and explain),
so suggest_portfolio can use any profile without a chain of if/else.
See the src/strategy.py section of CONTRACT.md and Decisions D7 and D8.
This is a stub: the names and types are final; the code comes in task C2.
"""

from abc import ABC, abstractmethod

from src import analysis  # suggest_portfolio uses allocate_dollars, portfolio_return, final_value (C2)
from src.models import Portfolio, StockStats


class ProfileStrategy(ABC):
    """The interface every risk profile follows."""

    name: str  # "Conservative", "Balanced", or "Growth"

    @abstractmethod
    def select(self, stats: list[StockStats]) -> dict[str, float]:
        """Return {ticker: weight} for exactly 4 tickers; the weights add up to 1."""

    @abstractmethod
    def explain(self, stats: list[StockStats], weights: dict[str, float]) -> tuple[str, str]:
        """Return (why_selected, profile_effect) as short plain-English texts."""


class ConservativeStrategy(ProfileStrategy):
    """The Conservative profile. Its rules are Decisions D7 and D8."""

    name = "Conservative"

    def select(self, stats: list[StockStats]) -> dict[str, float]:
        raise NotImplementedError("C2 (Chelsea): due Wed 11/25, 12:00 PM")

    def explain(self, stats: list[StockStats], weights: dict[str, float]) -> tuple[str, str]:
        raise NotImplementedError("C2 (Chelsea): due Wed 11/25, 12:00 PM")


class BalancedStrategy(ProfileStrategy):
    """The Balanced profile. Its rules are Decisions D7 and D8."""

    name = "Balanced"

    def select(self, stats: list[StockStats]) -> dict[str, float]:
        raise NotImplementedError("C2 (Chelsea): due Wed 11/25, 12:00 PM")

    def explain(self, stats: list[StockStats], weights: dict[str, float]) -> tuple[str, str]:
        raise NotImplementedError("C2 (Chelsea): due Wed 11/25, 12:00 PM")


class GrowthStrategy(ProfileStrategy):
    """The Growth profile. Its rules are Decisions D7 and D8."""

    name = "Growth"

    def select(self, stats: list[StockStats]) -> dict[str, float]:
        raise NotImplementedError("C2 (Chelsea): due Wed 11/25, 12:00 PM")

    def explain(self, stats: list[StockStats], weights: dict[str, float]) -> tuple[str, str]:
        raise NotImplementedError("C2 (Chelsea): due Wed 11/25, 12:00 PM")


# Every subclass above defines both methods, so Python lets us create them here.
STRATEGIES: dict[str, ProfileStrategy] = {
    "Conservative": ConservativeStrategy(),
    "Balanced": BalancedStrategy(),
    "Growth": GrowthStrategy(),
}


def suggest_portfolio(profile: str, stats: list[StockStats], amount: float) -> Portfolio:
    """Build the suggested Portfolio for one risk profile and amount.

    Steps: pick STRATEGIES[profile], get the weights with select(), then use
    analysis.allocate_dollars, analysis.portfolio_return, analysis.final_value,
    and explain() to fill in the Portfolio.
    """
    raise NotImplementedError("C2 (Chelsea): due Wed 11/25, 12:00 PM")


def check_rules(portfolio: Portfolio) -> list[str]:
    """Return a list of the hard rules (CONTRACT.md) that portfolio breaks.

    An empty list means every rule passes.
    """
    raise NotImplementedError("C2 (Chelsea): due Wed 11/25, 12:00 PM")

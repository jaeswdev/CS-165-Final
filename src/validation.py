"""Logic layer: check what the user typed (owner: Anahi).

See the src/validation.py section of CONTRACT.md, which lists the order of the
checks and the exact error messages.
This is a stub: the names and types are final; the code comes in task A1.
"""

PROFILES: tuple[str, ...] = ("Conservative", "Balanced", "Growth")
MIN_AMOUNT: float = 1.00
MAX_AMOUNT: float = 10_000_000.00


def parse_amount(text: str | None) -> tuple[float | None, str | None]:
    """Turn the amount the user typed into a number.

    Returns (amount, None) if the text is valid, or (None, message) if not.
    Allows spaces around the number, one leading "$", and commas, as in "$1,000.50".
    """
    raise NotImplementedError("A1 (Anahi): due Tue 11/24, 12:00 PM")


def validate_profile(value: str | None) -> tuple[str | None, str | None]:
    """Return (profile, None) if value is one of PROFILES, or (None, message) if not."""
    raise NotImplementedError("A1 (Anahi): due Tue 11/24, 12:00 PM")

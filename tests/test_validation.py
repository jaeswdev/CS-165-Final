"""each bad input give exactly the message listed in contract.md,
and not amount. Vald inputs must give the right number and no message."""

import pytest

from src.validation import(
    MAX_AMOUNT,
    MIN_AMOUNT,
    PROFILES,
    parse_amount,
    validate_profile,
)
BLANK = "Please enter an investment amount."
NEGATIVE = "The amount must be more than $0."
NOT_NUMBER = "Please enter a number, like 1000 or 1,000.50."
DECIMALS = "Please use at most 2 decimal places."
TOO_SMALL = "The amount must be at least $1.00."
TOO_LARGE = "Please enter $10,000,000 or less."
PROFILE = "Please choose Conservative, Balanced, or Growth."

@pytest.mark.unit
@pytest.mark.parametrize(
    "text, expected",
    [
        ("1000", 1000.00),
        ("1,000", 1000.00),
        ("$1,000.50", 1000.50),
        (" 250 ", 250.00),
        ("1", 1.00), #exactly the minimum
        ("1.00", 1.00),
        ("10000000", 10_000_000.00), #exactly the maximum
        ("$10,000,000.00", 10_000_000.00),
        ("99.9", 99.90), #one decimal place is fine
        ("2500.", 2500.00), #trailing point is fine
    ],
)
def test_valid_amounts(text, expected):
    amount, message = parse_amount(text)
    assert message is None
    assert amount == pytest.approx(expected)
    
@pytest.mark.negative
@pytest.mark.parametrize(
    "text, expected_message",
    [
        # 1. blank
        ("", BLANK),
        ("   ", BLANK),
        (None, BLANK),
        # 2. negative
        ("-50", NEGATIVE),
        ("$-50", NEGATIVE),
        ("-$50", NEGATIVE),
        (" -0.01 ", NEGATIVE),
        # 3. not a number
        ("abc", NOT_NUMBER),
        ("12a", NOT_NUMBER),
        ("1.2.3", NOT_NUMBER),
        ("1e5", NOT_NUMBER),
        ("nan", NOT_NUMBER),
        ("NaN", NOT_NUMBER),
        ("inf", NOT_NUMBER),
        ("1_000", NOT_NUMBER),
        ("$", NOT_NUMBER),
        ("$$50", NOT_NUMBER),
        ("1 000", NOT_NUMBER),
        ("+50", NOT_NUMBER),
        # 4. too many decimals
        ("10.123", DECIMALS),
        ("1,000.999", DECIMALS),
        # 5. below the minimum
        ("0", TOO_SMALL),
        ("0.50", TOO_SMALL),
        ("0.99", TOO_SMALL),
        # 6. above the maximum
        ("10000000.01", TOO_LARGE),
        ("99999999999", TOO_LARGE),
    ],
)
def test_bad_amounts_give_the_exact_message(text, expected_message):
    amount, message = parse_amount(text)
    assert amount is None
    assert message == expected_message


@pytest.mark.unit
def test_limits_match_the_contract():
    assert MIN_AMOUNT == 1.00
    assert MAX_AMOUNT == 10_000_000.00
    assert PROFILES == ("Conservative", "Balanced", "Growth")


@pytest.mark.unit
@pytest.mark.parametrize("profile", ["Conservative", "Balanced", "Growth"])
def test_valid_profiles(profile):
    assert validate_profile(profile) == (profile, None)


@pytest.mark.negative
@pytest.mark.parametrize("value", ["", None, "growth", "Aggressive", " Growth"])
def test_bad_profiles(value):
    assert validate_profile(value) == (None, PROFILE)


@pytest.mark.regression
def test_same_input_gives_same_result():
    assert parse_amount("$1,234.56") == parse_amount("$1,234.56") == (1234.56, None)    
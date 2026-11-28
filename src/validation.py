import re
from decimal import Decimal

PROFILES: tuple[str, ...] = ("Conservative", "Balanced", "Growth")
MIN_AMOUNT: float = 1.00
MAX_AMOUNT: float = 10_000_000.00

MSG_BLANK = "Please enter an investment amount."
MSG_NEGATIVE = "The amount must be more than $0."
MSG_NOT_NUMBER = "Please enter a number, like 1000 or 1,000.50."
MSG_DECIMALS = "Please use at most 2 decimal places."
MSG_TOO_SMALL = "The amount must be at least $1.00."
MSG_TOO_LARGE = "Please enter $10,000,000 or less."
MSG_PROFILE = "Please choose Conservative, Balanced, or Growth."

#this rejects "1e5", "nan", "inf", "1_000", and "1.2.3", which
#python float() would accept or mishandle

_NUMBER = re.compile(r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)")
def parse_amount(text:str|None) -> tuple[float| None, str| None]:
    """turns the amount of the user typed into a  number.
    Returns (amount, None) if the text is valid, or (None, message) 
    if not.
    Allows spaces around the number, one leading "$", and commas, as in "1,00.50"""
    
    #1. blank or only spaces
    if text is None or text.strip() == "":
        return None, MSG_BLANK
    cleaned = text.strip()
    
    #2. minus sign before any number
    if cleaned.startswith("-") or cleaned.startswith("$-"):
        return None, MSG_NEGATIVE
    
    #3. not a number
    if cleaned.startswith("$"):
        cleaned = cleaned[1:]
    cleaned = cleaned.replace(",", "")
    if not _NUMBER.fullmatch(cleaned):
        return None, MSG_NOT_NUMBER
    
    #4. more than 2 decimals
    if "." in cleaned and len(cleaned.split(".")[1]) > 2:
        return None, MSG_DECIMALS
    value = Decimal(cleaned)
    
    #5.zero, or less than $1
    if value < Decimal ("1.00"):
        return None, MSG_TOO_SMALL
    
    #6.more than $10,000,000
    if value > Decimal("10000000.00"):
        return None, MSG_TOO_LARGE
    return round(float(value), 2), None

def validate_profile(value: str|None) -> tuple[str|None, str|None]:
    """return (profile,None) if value is one of profiles, or 
    (None, message) if not.
    the match is exact, so "growth" (lower case) is not accepted.
    The slect box in app.py only offers the exact names, so 
    a user never types this"""
    
    #7. profile missing or not in profiles
    if value in PROFILES:
        return value, None
    return None, MSG_PROFILE

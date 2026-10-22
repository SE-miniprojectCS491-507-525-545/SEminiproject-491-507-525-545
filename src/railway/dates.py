"""Shared date parsing, so search and availability read dates the same way."""
from datetime import date, datetime


def to_date(value, error=ValueError):
    """Accept a date, a datetime or 'YYYY-MM-DD' text and return a date.

    `error` is the exception class raised for a missing or invalid date.
    """
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None or not str(value).strip():
        raise error("Travel date is required.")
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        raise error("Travel date must be a valid date (YYYY-MM-DD).") from None

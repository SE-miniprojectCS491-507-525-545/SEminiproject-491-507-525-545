"""Timing helper for the search response-time requirement (NFR-01).

NFR-01: a train search must respond within 5 seconds.
"""
import time

SEARCH_TIME_LIMIT_SECONDS = 5.0


def timed(function, *args, **kwargs):
    """Call function(*args, **kwargs) and return (result, seconds_taken)."""
    started = time.perf_counter()
    result = function(*args, **kwargs)
    return result, time.perf_counter() - started


def within_limit(seconds, limit=SEARCH_TIME_LIMIT_SECONDS):
    """True if `seconds` meets the NFR-01 limit."""
    return seconds <= limit
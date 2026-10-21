import re
from datetime import date, datetime

import pytest

from railway.search import SearchError, validate_search

TODAY = date(2026, 10, 21)
TRAVEL = date(2026, 11, 2)
STATIONS = ["Bengaluru", "Chennai", "Delhi"]


def check(source="Bengaluru", destination="Chennai", travel_date=TRAVEL, stations=STATIONS):
    return validate_search(source, destination, travel_date, stations, today=TODAY)


def test_valid_input_returns_cleaned_lowercase_names():
    assert check() == ("bengaluru", "chennai")


def test_names_are_trimmed_and_case_insensitive():
    assert check("  BENGALURU ", "chEnnai") == ("bengaluru", "chennai")


def test_station_list_entries_are_trimmed_too():
    assert check(stations=[" Bengaluru ", "Chennai "]) == ("bengaluru", "chennai")


def test_today_is_allowed():
    assert check(travel_date=TODAY) == ("bengaluru", "chennai")


@pytest.mark.parametrize("value", ["2026-11-02", " 2026-11-02 ", datetime(2026, 11, 2, 9, 0)])
def test_date_can_be_text_or_datetime(value):
    assert check(travel_date=value) == ("bengaluru", "chennai")


@pytest.mark.parametrize("source,destination,travel_date,message", [
    ("", "Chennai", TRAVEL, "Source station is required."),
    ("   ", "Chennai", TRAVEL, "Source station is required."),
    (None, "Chennai", TRAVEL, "Source station is required."),
    ("Bengaluru", "", TRAVEL, "Destination station is required."),
    ("Bengaluru", None, TRAVEL, "Destination station is required."),
    ("Bengaluru", "Chennai", None, "Travel date is required."),
    ("Bengaluru", "Chennai", "", "Travel date is required."),
    ("Bengaluru", "Chennai", "   ", "Travel date is required."),
    ("Bengaluru", "Chennai", "02-11-2026", "Travel date must be a valid date (YYYY-MM-DD)."),
    ("Bengaluru", "Chennai", "2026-02-30", "Travel date must be a valid date (YYYY-MM-DD)."),
    ("Bengaluru", "Chennai", "soon", "Travel date must be a valid date (YYYY-MM-DD)."),
    ("Atlantis", "Chennai", TRAVEL, "Unknown station: Atlantis."),
    ("Bengaluru", "Narnia", TRAVEL, "Unknown station: Narnia."),
    ("Delhi", "delhi", TRAVEL, "Source and destination cannot be the same."),
    ("Bengaluru", "Chennai", date(2026, 10, 20), "Travel date cannot be in the past."),
    ("Bengaluru", "Chennai", "2026-10-20", "Travel date cannot be in the past."),
])
def test_invalid_input_is_rejected_with_a_clear_message(source, destination, travel_date, message):
    with pytest.raises(SearchError, match=re.escape(message)):
        check(source, destination, travel_date)


def test_missing_source_is_reported_before_unknown_station():
    with pytest.raises(SearchError, match="Source station is required"):
        check("", "Narnia")


def test_empty_station_list_means_every_station_is_unknown():
    with pytest.raises(SearchError, match="Unknown station"):
        check(stations=[])
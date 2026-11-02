from datetime import date

import pytest

from railway.models import Train
from railway.search_help import (
    friendly_date,
    no_results_hint,
    suggest_stations,
    unknown_station_hint,
)

TODAY = date(2026, 10, 24)           # a Saturday
STATIONS = ["Bengaluru", "Delhi", "Mysuru", "Mumbai"]
ALL = tuple(range(7))
TRAINS = [
    Train("1", "A", "Bengaluru", "Delhi", "19:20", (0, 2)),      # Mon, Wed only
    Train("2", "B", "Bengaluru", "Mysuru", "08:30", ALL),
]


def test_today_and_tomorrow_words_work_in_any_case():
    assert friendly_date("today", TODAY) == TODAY
    assert friendly_date(" Tomorrow ", TODAY) == date(2026, 10, 25)


def test_iso_dates_still_work():
    assert friendly_date("2026-11-02", TODAY) == date(2026, 11, 2)


@pytest.mark.parametrize("text,message", [
    ("", "Travel date is required."),
    ("   ", "Travel date is required."),
    (None, "Travel date is required."),
    ("02/11/2026", "Travel date must be in YYYY-MM-DD format."),
    ("next week", "Travel date must be in YYYY-MM-DD format."),
])
def test_bad_dates_give_the_usual_messages(text, message):
    with pytest.raises(ValueError) as err:
        friendly_date(text, TODAY)
    assert str(err.value) == message


def test_typo_gets_a_suggestion():
    assert suggest_stations("Bengaluro", STATIONS) == ["Bengaluru"]
    assert suggest_stations("dehli", STATIONS) == ["Delhi"]


def test_partial_name_gets_a_suggestion_and_prefix_comes_first():
    assert suggest_stations("mum", STATIONS)[0] == "Mumbai"
    assert suggest_stations("m", STATIONS) == ["Mumbai", "Mysuru"]


def test_nothing_close_gives_no_suggestions():
    assert suggest_stations("Atlantis", STATIONS) == []
    assert suggest_stations("", STATIONS) == []


def test_unknown_station_hint_is_never_empty():
    assert unknown_station_hint("dehli", STATIONS) == "Did you mean: Delhi?"
    assert "list above" in unknown_station_hint("Atlantis", STATIONS)


def test_no_results_hint_names_the_days_a_route_runs():
    assert no_results_hint(TRAINS, "bengaluru", "DELHI") == \
        "This route runs on: Monday, Wednesday. Try one of those days."


def test_no_results_hint_lists_where_you_can_go_from_the_source():
    hint = no_results_hint(TRAINS, "Bengaluru", "Mumbai")
    assert "From Bengaluru you can go to: Delhi, Mysuru." in hint


def test_no_results_hint_when_nothing_leaves_the_source():
    assert no_results_hint(TRAINS, "Mumbai", "Delhi") == "No trains leave from Mumbai."
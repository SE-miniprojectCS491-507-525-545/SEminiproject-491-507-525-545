from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from railway.models import Train as SharedTrain
from railway.search import SearchError, Train, search_trains, stations_of

TODAY = date(2026, 10, 21)
MON, TUE, SUN = date(2026, 11, 2), date(2026, 11, 3), date(2026, 11, 8)

KARNATAKA = Train("12627", "Karnataka Express", "Bengaluru", "Delhi", "19:20", (0, 2, 4))
RETURN = Train("12628", "Return Express", "Delhi", "Bengaluru", "08:00", (1, 3, 5))
RAJDHANI = Train("20001", "Rajdhani", "Bengaluru", "Delhi", "06:00", (0, 1, 2, 3, 4, 5, 6))
TRAINS = [KARNATAKA, RETURN, RAJDHANI]
STATIONS = ["Bengaluru", "Delhi", "Chennai"]


def find(source, destination, day):
    return search_trains(source, destination, day, TRAINS, STATIONS, today=TODAY)


def test_returns_matching_trains_in_the_order_given():
    assert find("Bengaluru", "Delhi", MON) == [KARNATAKA, RAJDHANI]


def test_only_trains_running_on_that_weekday_are_returned():
    assert find("Bengaluru", "Delhi", TUE) == [RAJDHANI]
    assert find("Bengaluru", "Delhi", SUN) == [RAJDHANI]


def test_search_is_directional():
    assert find("Delhi", "Bengaluru", TUE) == [RETURN]
    assert find("Delhi", "Bengaluru", MON) == []


def test_station_names_are_case_and_space_insensitive():
    assert find("  bengaluru", "DELHI ", MON) == [KARNATAKA, RAJDHANI]


def test_known_stations_with_no_service_give_an_empty_list():
    assert find("Bengaluru", "Chennai", MON) == []


def test_date_can_be_given_as_text():
    assert find("Bengaluru", "Delhi", "2026-11-02") == [KARNATAKA, RAJDHANI]


def test_invalid_search_raises_search_error():
    with pytest.raises(SearchError):
        find("Bengaluru", "Bengaluru", MON)
    with pytest.raises(SearchError):
        find("Bengaluru", "Delhi", date(2026, 10, 1))


def test_stations_of_lists_every_station_once_sorted():
    assert stations_of(TRAINS) == ["Bengaluru", "Delhi"]
    assert stations_of([]) == []


def test_search_uses_the_shared_train_model():
    assert Train is SharedTrain


def test_train_is_immutable():
    with pytest.raises(FrozenInstanceError):
        KARNATAKA.name = "Changed"
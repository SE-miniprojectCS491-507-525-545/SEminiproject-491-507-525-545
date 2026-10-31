"""NFR-01: a train search responds within 5 seconds.

These tests build a database far bigger than the demo (20,000 trains over 200
stations) and time the same steps the CLI runs for option 4: load the trains,
validate and search, then look up seat availability for every result.
The limit asserted is the real requirement (5 s), so they only fail on a
genuine slowdown, not on a slightly slow laptop.
"""
from datetime import date

import pytest

from railway import storage
from railway.availability import list_availability
from railway.perf import SEARCH_TIME_LIMIT_SECONDS, timed, within_limit
from railway.search import search_trains, stations_of

TODAY = date(2026, 10, 24)
TRAVEL_DAY = date(2026, 11, 2)
ALL_DAYS = "0,1,2,3,4,5,6"
STATIONS = [f"City{i}" for i in range(200)]
TRAIN_COUNT = 20_000
BUSY_ROUTE = ("City3", "City24")
BUSY_ROUTE_TRAINS = 300          # many trains on ONE route -> many results to price


def _fill(conn):
    rows, classes = [], []
    for i in range(TRAIN_COUNT):
        src = STATIONS[i % 200]
        dst = STATIONS[(i * 7 + 3) % 200]
        if src == dst:
            dst = STATIONS[(i + 1) % 200]
        if i < BUSY_ROUTE_TRAINS:
            src, dst = BUSY_ROUTE
        number = f"T{i:05d}"
        rows.append((number, f"Train {i}", src, dst, "10:00", ALL_DAYS))
        classes.append((number, "SL", 100, 500.0))
        classes.append((number, "3AC", 50, 1200.0))
    with conn:
        conn.executemany("INSERT INTO trains VALUES (?,?,?,?,?,?)", rows)
        conn.executemany("INSERT INTO seat_classes VALUES (?,?,?,?)", classes)


@pytest.fixture(scope="module")
def big_conn(tmp_path_factory):
    path = tmp_path_factory.mktemp("perf") / "big.db"      # a real file, like production
    conn = storage.connect(str(path))
    _fill(conn)
    yield conn
    conn.close()


def _search(conn, source, destination):
    trains = storage.list_trains(conn)
    return search_trains(source, destination, TRAVEL_DAY, trains,
                         stations_of(trains), today=TODAY)


def test_search_over_20000_trains_is_within_5_seconds(big_conn):
    found, seconds = timed(_search, big_conn, "City5", "City38")
    assert within_limit(seconds), f"search took {seconds:.2f}s (limit {SEARCH_TIME_LIMIT_SECONDS}s)"
    assert isinstance(found, list)


def test_search_with_hundreds_of_results_incl_seat_lookup_is_within_5_seconds(big_conn):
    def search_and_price():
        found = _search(big_conn, *BUSY_ROUTE)
        return [list_availability(big_conn, t.number, TRAVEL_DAY, today=TODAY) for t in found]

    priced, seconds = timed(search_and_price)
    assert len(priced) >= BUSY_ROUTE_TRAINS
    assert all(len(classes) == 2 for classes in priced)
    assert within_limit(seconds), f"search took {seconds:.2f}s (limit {SEARCH_TIME_LIMIT_SECONDS}s)"


def test_search_with_no_matches_is_within_5_seconds(big_conn):
    found, seconds = timed(_search, big_conn, "City1", "City2")
    assert found == []
    assert within_limit(seconds)


def test_timed_returns_result_and_elapsed_time():
    result, seconds = timed(lambda x: x * 2, 21)
    assert result == 42
    assert 0 <= seconds < 1


def test_within_limit_boundaries():
    assert within_limit(0)
    assert within_limit(5.0)
    assert not within_limit(5.01)
    assert within_limit(9, limit=10)
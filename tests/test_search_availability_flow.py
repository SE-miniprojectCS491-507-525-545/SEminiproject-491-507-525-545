"""Sprint 1 flow: trains in the database -> search -> seat availability."""
from datetime import date

import pytest

from railway import storage
from railway.availability import (
    AVAILABLE,
    SOLD_OUT,
    AvailabilityError,
    check_availability,
    list_availability,
)
from railway.models import SeatClass, Train
from railway.search import SearchError, search_trains, stations_of

TODAY = date(2026, 10, 21)
MON = date(2026, 11, 2)      # 12627 runs Mon/Wed/Fri
TUE = date(2026, 11, 3)      # 12628 runs Tue/Thu/Sat


def seed(conn):
    storage.add_train(
        conn,
        Train("12627", "Karnataka Express", "Bengaluru", "Delhi", "19:20", (0, 2, 4)),
        [SeatClass("12627", "3AC", 60, 1500.0), SeatClass("12627", "SL", 120, 600.0)],
    )
    storage.add_train(
        conn,
        Train("12628", "Return Express", "Delhi", "Bengaluru", "08:00", (1, 3, 5)),
        [SeatClass("12628", "SL", 100, 650.0)],
    )


@pytest.fixture
def conn():
    c = storage.connect(":memory:")
    seed(c)
    yield c
    c.close()


def find(conn, source, destination, day):
    trains = storage.list_trains(conn)
    return search_trains(source, destination, day, trains, stations_of(trains), today=TODAY)


def test_search_finds_train_and_availability_shows_all_seats_free(conn):
    (train,) = find(conn, "Bengaluru", "Delhi", MON)
    assert train.number == "12627"
    rows = list_availability(conn, train.number, MON, today=TODAY)
    assert [(r.seat_class, r.free_seats, r.status) for r in rows] == [
        ("3AC", 60, AVAILABLE), ("SL", 120, AVAILABLE)]


def test_availability_changes_are_visible_on_the_next_check(conn):
    storage.set_availability(conn, "12627", MON, "3AC", 58)
    assert check_availability(conn, "12627", MON, "3AC", today=TODAY).free_seats == 58


def test_sold_out_train_is_still_found_but_reported_sold_out(conn):
    storage.set_availability(conn, "12627", MON, "SL", 0)
    assert [t.number for t in find(conn, "Bengaluru", "Delhi", MON)] == ["12627"]
    assert check_availability(conn, "12627", MON, "SL", today=TODAY).status == SOLD_OUT


def test_search_and_availability_agree_on_running_days(conn):
    assert find(conn, "Bengaluru", "Delhi", TUE) == []
    with pytest.raises(AvailabilityError, match="does not run"):
        check_availability(conn, "12627", TUE, "3AC", today=TODAY)


def test_return_journey_is_found_on_its_own_days(conn):
    assert [t.number for t in find(conn, "Delhi", "Bengaluru", TUE)] == ["12628"]
    assert find(conn, "Delhi", "Bengaluru", MON) == []


def test_train_added_later_shows_up_in_search(conn):
    storage.add_train(
        conn,
        Train("20001", "Rajdhani", "Bengaluru", "Delhi", "06:00", tuple(range(7))),
        [SeatClass("20001", "2AC", 40, 2800.0)],
    )
    assert [t.number for t in find(conn, "Bengaluru", "Delhi", MON)] == ["12627", "20001"]


def test_invalid_search_is_rejected_before_any_availability_lookup(conn):
    with pytest.raises(SearchError, match="Unknown station"):
        find(conn, "Bengaluru", "Narnia", MON)


def test_data_survives_closing_and_reopening_the_database(tmp_path):
    path = str(tmp_path / "railway.db")
    first = storage.connect(path)
    seed(first)
    storage.set_availability(first, "12627", MON, "3AC", 41)
    first.close()

    second = storage.connect(path)
    assert [t.number for t in find(second, "Bengaluru", "Delhi", MON)] == ["12627"]
    assert check_availability(second, "12627", MON, "3AC", today=TODAY).free_seats == 41
    second.close()
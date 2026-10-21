from datetime import date, datetime

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

TODAY = date(2026, 10, 21)
MONDAY = date(2026, 11, 2)      # train runs Mon, Wed, Fri
TUESDAY = date(2026, 11, 3)


@pytest.fixture
def conn():
    c = storage.connect(":memory:")
    storage.add_train(
        c,
        Train("12627", "Karnataka Express", "Bengaluru", "Delhi", "19:20", (0, 2, 4)),
        [SeatClass("12627", "3AC", 60, 1500.0), SeatClass("12627", "SL", 120, 600.0)],
    )
    yield c
    c.close()


def test_unrecorded_availability_means_all_seats_free(conn):
    info = check_availability(conn, "12627", MONDAY, "3AC", today=TODAY)
    assert (info.total_seats, info.free_seats) == (60, 60)
    assert info.status == AVAILABLE
    assert info.fare == 1500.0


def test_recorded_availability_is_returned(conn):
    storage.set_availability(conn, "12627", MONDAY, "3AC", 10)
    assert check_availability(conn, "12627", MONDAY, "3AC", today=TODAY).free_seats == 10


def test_availability_follows_updates(conn):
    storage.set_availability(conn, "12627", MONDAY, "3AC", 10)
    storage.set_availability(conn, "12627", MONDAY, "3AC", 7)
    assert check_availability(conn, "12627", MONDAY, "3AC", today=TODAY).free_seats == 7


def test_zero_free_seats_is_sold_out(conn):
    storage.set_availability(conn, "12627", MONDAY, "3AC", 0)
    info = check_availability(conn, "12627", MONDAY, "3AC", today=TODAY)
    assert info.free_seats == 0
    assert info.status == SOLD_OUT


def test_each_date_and_class_is_independent(conn):
    storage.set_availability(conn, "12627", MONDAY, "3AC", 5)
    assert check_availability(conn, "12627", date(2026, 11, 4), "3AC", today=TODAY).free_seats == 60
    assert check_availability(conn, "12627", MONDAY, "SL", today=TODAY).free_seats == 120


def test_class_and_train_number_are_trimmed_and_case_insensitive(conn):
    info = check_availability(conn, " 12627 ", MONDAY, " 3ac ", today=TODAY)
    assert info.seat_class == "3AC"


@pytest.mark.parametrize("value", ["2026-11-02", date(2026, 11, 2), datetime(2026, 11, 2, 9, 30)])
def test_date_can_be_string_date_or_datetime(conn, value):
    assert check_availability(conn, "12627", value, "SL", today=TODAY).travel_date == MONDAY


def test_today_is_allowed(conn):
    storage.add_train(conn, Train("T1", "Daily", "A", "B", "10:00", tuple(range(7))),
                      [SeatClass("T1", "SL", 10, 100.0)])
    assert check_availability(conn, "T1", TODAY, "SL", today=TODAY).free_seats == 10


@pytest.mark.parametrize("train_number", ["99999", "", "   ", None])
def test_unknown_train_is_rejected(conn, train_number):
    with pytest.raises(AvailabilityError, match="not found"):
        check_availability(conn, train_number, MONDAY, "3AC", today=TODAY)


@pytest.mark.parametrize("seat_class", ["1AC", "", None])
def test_class_not_on_train_is_rejected(conn, seat_class):
    with pytest.raises(AvailabilityError, match="Choose from: 3AC, SL"):
        check_availability(conn, "12627", MONDAY, seat_class, today=TODAY)


def test_train_not_running_on_that_weekday_is_rejected(conn):
    with pytest.raises(AvailabilityError, match="does not run on 2026-11-03 \\(Tuesday\\)"):
        check_availability(conn, "12627", TUESDAY, "3AC", today=TODAY)


def test_past_date_is_rejected(conn):
    with pytest.raises(AvailabilityError, match="past"):
        check_availability(conn, "12627", date(2026, 10, 19), "3AC", today=TODAY)


@pytest.mark.parametrize("bad", ["", None, "02-11-2026", "2026-02-30", "soon"])
def test_bad_date_is_rejected(conn, bad):
    with pytest.raises(AvailabilityError):
        check_availability(conn, "12627", bad, "3AC", today=TODAY)


def test_list_availability_covers_every_class(conn):
    storage.set_availability(conn, "12627", MONDAY, "3AC", 0)
    result = list_availability(conn, "12627", MONDAY, today=TODAY)
    assert [(a.seat_class, a.free_seats, a.status) for a in result] == [
        ("3AC", 0, SOLD_OUT), ("SL", 120, AVAILABLE)]


def test_list_availability_validates_train_and_day(conn):
    with pytest.raises(AvailabilityError, match="not found"):
        list_availability(conn, "99999", MONDAY, today=TODAY)
    with pytest.raises(AvailabilityError, match="does not run"):
        list_availability(conn, "12627", TUESDAY, today=TODAY)
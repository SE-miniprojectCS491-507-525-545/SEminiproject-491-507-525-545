from dataclasses import dataclass
from datetime import date, datetime

import pytest

from railway.cancellation import (
    CANCELLED,
    CancellationError,
    cancel_ticket,
    validate_cancellation,
    validate_deadline,
)
from railway.search import Train

TRAVEL = date(2026, 11, 2)
TRAINS = [
    Train("12627", "Karnataka Express", "Bengaluru", "Delhi", "06:00", (0, 1, 2, 3, 4, 5, 6)),
]
NOW = datetime(2026, 10, 30, 9, 0)  # well before departure
KEY = ("12627", TRAVEL, "3AC")


@dataclass
class FakeBooking:
    status: str = "CONFIRMED"
    train_number: str = "12627"
    travel_date: date = TRAVEL
    seat_class: str = "3AC"
    passengers: int = 2


@pytest.fixture
def bookings():
    return {
        "PNR1001": FakeBooking("CONFIRMED"),
        "PNR1002": FakeBooking("CANCELLED"),
    }


@pytest.fixture
def availability():
    return {KEY: 10}


# --- FR-08: validation ---

def test_valid_pnr_returns_booking(bookings):
    assert validate_cancellation("PNR1001", bookings) is bookings["PNR1001"]


def test_pnr_with_spaces_is_cleaned(bookings):
    assert validate_cancellation("  PNR1001  ", bookings) is bookings["PNR1001"]


@pytest.mark.parametrize("pnr", ["", "   ", None])
def test_empty_pnr_rejected(pnr, bookings):
    with pytest.raises(CancellationError, match="PNR is required"):
        validate_cancellation(pnr, bookings)


def test_unknown_pnr_rejected(bookings):
    with pytest.raises(CancellationError, match="No booking found"):
        validate_cancellation("PNR9999", bookings)


def test_already_cancelled_rejected(bookings):
    with pytest.raises(CancellationError, match="already cancelled"):
        validate_cancellation("PNR1002", bookings)


# --- FR-06: cancel ticket ---

def test_cancel_marks_booking_cancelled(bookings, availability):
    cancel_ticket("PNR1001", bookings, availability, TRAINS, NOW)
    assert bookings["PNR1001"].status == CANCELLED


def test_cancel_releases_seats(bookings, availability):
    cancel_ticket("PNR1001", bookings, availability, TRAINS, NOW)
    assert availability[KEY] == 12


def test_cancel_creates_availability_entry_if_missing(bookings):
    availability = {}
    cancel_ticket("PNR1001", bookings, availability, TRAINS, NOW)
    assert availability[KEY] == 2


def test_cancel_returns_confirmation(bookings, availability):
    result = cancel_ticket(
        "PNR1001", bookings, availability, TRAINS, NOW, refund_amount=500.0
    )
    assert result.pnr == "PNR1001"
    assert result.seats_released == 2
    assert result.refund_amount == 500.0


def test_cancel_same_pnr_twice_refused(bookings, availability):
    cancel_ticket("PNR1001", bookings, availability, TRAINS, NOW)
    with pytest.raises(CancellationError, match="already cancelled"):
        cancel_ticket("PNR1001", bookings, availability, TRAINS, NOW)
    assert availability[KEY] == 12


def test_invalid_cancel_leaves_seats_unchanged(bookings, availability):
    with pytest.raises(CancellationError):
        cancel_ticket("PNR9999", bookings, availability, TRAINS, NOW)
    assert availability[KEY] == 10


# --- BR-02: 4-hour deadline ---

def test_deadline_allows_cancel_well_before_departure():
    validate_deadline(TRAVEL, "06:00", datetime(2026, 11, 1, 6, 0))


def test_deadline_allows_exactly_four_hours_before():
    validate_deadline(TRAVEL, "06:00", datetime(2026, 11, 2, 2, 0))


@pytest.mark.parametrize(
    "now",
    [
        datetime(2026, 11, 2, 2, 1),  # 3 hours 59 minutes before
        datetime(2026, 11, 2, 7, 0),  # after departure
    ],
)
def test_deadline_refuses_inside_four_hours(now):
    with pytest.raises(CancellationError, match="4 hours before departure"):
        validate_deadline(TRAVEL, "06:00", now)


def test_cancel_refused_inside_deadline_changes_nothing(bookings, availability):
    too_late = datetime(2026, 11, 2, 3, 0)
    with pytest.raises(CancellationError, match="4 hours before departure"):
        cancel_ticket("PNR1001", bookings, availability, TRAINS, too_late)
    assert bookings["PNR1001"].status == "CONFIRMED"
    assert availability[KEY] == 10


def test_cancel_with_unknown_train_refused(availability):
    bookings = {"PNR2001": FakeBooking(train_number="99999")}
    with pytest.raises(CancellationError, match="Train 99999 not found"):
        cancel_ticket("PNR2001", bookings, availability, TRAINS, NOW)
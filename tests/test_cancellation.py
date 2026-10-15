from dataclasses import dataclass

import pytest

from railway.cancellation import (
    CANCELLED,
    CancellationError,
    cancel_ticket,
    validate_cancellation,
)


@dataclass
class FakeBooking:
    status: str = "CONFIRMED"
    train_number: str = "12627"
    travel_date: str = "2026-11-02"
    seat_class: str = "3AC"
    passengers: int = 2


KEY = ("12627", "2026-11-02", "3AC")


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
    cancel_ticket("PNR1001", bookings, availability)
    assert bookings["PNR1001"].status == CANCELLED


def test_cancel_releases_seats(bookings, availability):
    cancel_ticket("PNR1001", bookings, availability)
    assert availability[KEY] == 12


def test_cancel_creates_availability_entry_if_missing(bookings):
    availability = {}
    cancel_ticket("PNR1001", bookings, availability)
    assert availability[KEY] == 2


def test_cancel_returns_confirmation(bookings, availability):
    result = cancel_ticket("PNR1001", bookings, availability, refund_amount=500.0)
    assert result.pnr == "PNR1001"
    assert result.seats_released == 2
    assert result.refund_amount == 500.0


def test_cancel_same_pnr_twice_refused(bookings, availability):
    cancel_ticket("PNR1001", bookings, availability)
    with pytest.raises(CancellationError, match="already cancelled"):
        cancel_ticket("PNR1001", bookings, availability)
    assert availability[KEY] == 12


def test_invalid_cancel_leaves_seats_unchanged(bookings, availability):
    with pytest.raises(CancellationError):
        cancel_ticket("PNR9999", bookings, availability)
    assert availability[KEY] == 10
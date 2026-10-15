from dataclasses import dataclass

import pytest

from railway.cancellation import CancellationError, validate_cancellation


@dataclass
class FakeBooking:
    status: str = "CONFIRMED"


@pytest.fixture
def bookings():
    return {
        "PNR1001": FakeBooking("CONFIRMED"),
        "PNR1002": FakeBooking("CANCELLED"),
    }


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
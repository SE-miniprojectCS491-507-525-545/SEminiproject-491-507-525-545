from datetime import date

import pytest

from railway.access import (
    AccessError,
    can_access_booking,
    is_admin,
    require_admin,
    require_booking_access,
)
from railway.models import ROLE_ADMIN, Booking, Passenger

OWNER = Passenger("asha@example.com", "Asha", "hash")
OTHER = Passenger("ravi@example.com", "Ravi", "hash")
ADMIN = Passenger("admin@example.com", "Admin", "hash", ROLE_ADMIN)
BOOKING = Booking("PNR1001", "asha@example.com", "12627", date(2026, 11, 2), "3AC", 2, 1000.0)


def test_default_role_is_passenger():
    assert OWNER.role == "passenger"


def test_is_admin_true_for_admin():
    assert is_admin(ADMIN) is True


def test_is_admin_false_for_passenger():
    assert is_admin(OWNER) is False


def test_is_admin_false_when_not_logged_in():
    assert is_admin(None) is False


def test_require_admin_allows_admin():
    assert require_admin(ADMIN) is ADMIN


def test_require_admin_refuses_passenger():
    with pytest.raises(AccessError, match="Admin access required"):
        require_admin(OWNER)


def test_require_admin_refuses_when_not_logged_in():
    with pytest.raises(AccessError, match="Not logged in"):
        require_admin(None)


def test_owner_can_access_own_booking():
    assert can_access_booking(OWNER, BOOKING) is True


def test_other_passenger_cannot_access_booking():
    assert can_access_booking(OTHER, BOOKING) is False


def test_admin_can_access_any_booking():
    assert can_access_booking(ADMIN, BOOKING) is True


def test_email_match_ignores_case():
    shouty = Passenger("ASHA@Example.com", "Asha", "hash")
    assert can_access_booking(shouty, BOOKING) is True


@pytest.mark.parametrize("passenger,booking", [(None, BOOKING), (OWNER, None)])
def test_no_access_without_passenger_or_booking(passenger, booking):
    assert can_access_booking(passenger, booking) is False


def test_require_booking_access_returns_booking_for_owner():
    assert require_booking_access(OWNER, BOOKING) is BOOKING


def test_require_booking_access_refuses_other_passenger():
    with pytest.raises(AccessError, match="your own bookings"):
        require_booking_access(OTHER, BOOKING)


def test_require_booking_access_refuses_when_not_logged_in():
    with pytest.raises(AccessError, match="Not logged in"):
        require_booking_access(None, BOOKING)
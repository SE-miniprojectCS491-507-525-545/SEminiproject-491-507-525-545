from datetime import date

import pytest

from railway import storage
from railway.access import AccessError
from railway.booking_views import (
    BookingViewError,
    format_booking_details,
    format_booking_list,
    list_all_bookings,
    view_booking,
)
from railway.models import ROLE_ADMIN, Booking, Passenger, SeatClass, Train, Traveller

TRAIN = Train("12627", "Karnataka Express", "Bengaluru", "Delhi", "06:00", (0, 1, 2, 3, 4, 5, 6))
SEAT_CLASS = SeatClass("12627", "3AC", 50, 1000.0)
DAY = date(2026, 11, 2)

ASHA = Passenger("asha@example.com", "Asha Rao", "hash")
RAVI = Passenger("ravi@example.com", "Ravi Kumar", "hash")
ADMIN = Passenger("admin@example.com", "Admin", "hash", ROLE_ADMIN)

ASHA_BOOKING = Booking("PNR1001", "asha@example.com", "12627", DAY, "3AC", 1, 1000.0)
RAVI_BOOKING = Booking("PNR1002", "ravi@example.com", "12627", DAY, "3AC", 1, 1000.0)


@pytest.fixture
def conn():
    connection = storage.connect(":memory:")
    storage.add_train(connection, TRAIN, [SEAT_CLASS])
    for person in (ASHA, RAVI, ADMIN):
        storage.add_passenger(connection, person)
    storage.add_booking(connection, ASHA_BOOKING, [Traveller("Asha Rao", 30, "F")])
    storage.add_booking(connection, RAVI_BOOKING, [Traveller("Ravi Kumar", 41, "M")])
    yield connection
    connection.close()


@pytest.fixture
def empty_conn():
    connection = storage.connect(":memory:")
    storage.add_passenger(connection, ADMIN)
    yield connection
    connection.close()


# --- FR-11: view booking by PNR ---

def test_owner_can_view_own_booking(conn):
    details = view_booking(conn, "PNR1001", ASHA)
    assert details.booking.pnr == "PNR1001"
    assert details.train_name == "Karnataka Express"
    assert details.travellers[0].name == "Asha Rao"
    assert details.seat_numbers == ()


def test_pnr_with_spaces_is_cleaned(conn):
    assert view_booking(conn, "  PNR1001  ", ASHA).booking.pnr == "PNR1001"


def test_admin_can_view_any_booking(conn):
    assert view_booking(conn, "PNR1001", ADMIN).booking.passenger_email == "asha@example.com"


def test_passenger_cannot_view_someone_elses_booking(conn):
    with pytest.raises(BookingViewError, match="No booking found"):
        view_booking(conn, "PNR1002", ASHA)


@pytest.mark.parametrize("pnr", ["", "   ", None])
def test_empty_pnr_is_rejected(pnr, conn):
    with pytest.raises(BookingViewError, match="PNR is required"):
        view_booking(conn, pnr, ASHA)


def test_view_requires_login(conn):
    with pytest.raises(AccessError, match="Not logged in"):
        view_booking(conn, "PNR1001", None)


def test_unknown_pnr_is_rejected(conn):
    with pytest.raises(BookingViewError, match="No booking found"):
        view_booking(conn, "PNR9999", ASHA)


def test_viewing_changes_nothing(conn):
    view_booking(conn, "PNR1001", ASHA)
    assert storage.get_booking(conn, "PNR1001").status == "CONFIRMED"


# --- FR-15: admin views all bookings ---

def test_admin_sees_all_bookings_in_pnr_order(conn):
    bookings = list_all_bookings(conn, ADMIN)
    assert [b.pnr for b in bookings] == ["PNR1001", "PNR1002"]


def test_passenger_cannot_list_all_bookings(conn):
    with pytest.raises(AccessError, match="Admin access required"):
        list_all_bookings(conn, ASHA)


def test_list_all_requires_login(conn):
    with pytest.raises(AccessError, match="Not logged in"):
        list_all_bookings(conn, None)


def test_admin_sees_empty_list_when_no_bookings(empty_conn):
    assert list_all_bookings(empty_conn, ADMIN) == []


# --- display text ---

def test_booking_details_text_has_the_key_facts(conn):
    text = format_booking_details(view_booking(conn, "PNR1001", ASHA))
    assert "PNR1001" in text
    assert "Karnataka Express" in text
    assert "Asha Rao" in text
    assert "1000.00" in text


def test_empty_booking_list_text():
    assert format_booking_list([]) == "No bookings found."


def test_booking_list_text_has_one_line_per_booking(conn):
    lines = format_booking_list(list_all_bookings(conn, ADMIN)).splitlines()
    assert len(lines) == 2
    assert "asha@example.com" in lines[0]
"""Checks that modules written by different people work together."""
from datetime import date, datetime

import pytest

from railway import storage
from railway.auth import login
from railway.cancellation import CANCELLED, CancellationError, cancel_booking
from railway.models import Booking, Passenger, SeatClass, Train
from railway.registration import register_passenger

TRAVEL = date(2026, 11, 2)           # departs 19:20
EARLY = datetime(2026, 10, 21, 10, 0)  # about 12 days before: 10% fee


@pytest.fixture
def conn():
    c = storage.connect(":memory:")
    storage.add_train(c, Train("12627", "Karnataka Express", "Bengaluru", "Delhi",
                               "19:20", (0, 2, 4)),
                      [SeatClass("12627", "3AC", 60, 1500.0)])
    storage.add_passenger(c, Passenger("a@x.com", "Asha", "salt$hash"))
    storage.set_availability(c, "12627", TRAVEL, "3AC", 10)
    yield c
    c.close()


def booking(pnr="PNR1001", **kw):
    fields = dict(pnr=pnr, passenger_email="a@x.com", train_number="12627",
                  travel_date=TRAVEL, seat_class="3AC", passengers=2, fare=3000.0)
    fields.update(kw)
    return Booking(**fields)


# --- registration -> storage -> login ---

def test_registered_passenger_can_be_stored_and_used_to_log_in(conn):
    accounts = {}
    new = register_passenger("Ravi", "ravi@x.com", "Secret123", accounts)
    assert isinstance(new, Passenger) and new.role == "passenger"

    storage.add_passenger(conn, new)
    token = login("ravi@x.com", "Secret123", storage.load_passengers(conn), {})
    assert len(token) == 32


# --- cancel_booking (database version of cancel_ticket) ---

def test_cancel_booking_does_everything_in_one_call(conn):
    storage.add_booking(conn, booking())
    storage.add_seat_allocation(conn, "PNR1001", "12627", TRAVEL, "3AC", 14)

    result = cancel_booking(conn, "PNR1001", now=EARLY)

    assert (result.pnr, result.seats_released, result.refund_amount) == ("PNR1001", 2, 2700.0)
    assert storage.get_booking(conn, "PNR1001").status == CANCELLED
    assert storage.get_availability(conn, "12627", TRAVEL, "3AC") == 12
    assert storage.get_seat_numbers(conn, "PNR1001") == []


def test_cancel_booking_trims_the_pnr(conn):
    storage.add_booking(conn, booking())
    assert cancel_booking(conn, "  PNR1001 ", now=EARLY).pnr == "PNR1001"


@pytest.mark.parametrize("pnr", ["", "   ", "NOPE"])
def test_cancel_booking_rejects_empty_or_unknown_pnr(conn, pnr):
    with pytest.raises(CancellationError):
        cancel_booking(conn, pnr, now=EARLY)


def test_cancel_booking_rejects_a_second_cancellation(conn):
    storage.add_booking(conn, booking())
    cancel_booking(conn, "PNR1001", now=EARLY)
    with pytest.raises(CancellationError):
        cancel_booking(conn, "PNR1001", now=EARLY)
    assert storage.get_availability(conn, "12627", TRAVEL, "3AC") == 12


def test_cancel_booking_refuses_inside_four_hours_and_changes_nothing(conn):
    storage.add_booking(conn, booking())
    with pytest.raises(CancellationError):
        cancel_booking(conn, "PNR1001", now=datetime(2026, 11, 2, 16, 0))
    assert storage.get_booking(conn, "PNR1001").status == "CONFIRMED"
    assert storage.get_availability(conn, "12627", TRAVEL, "3AC") == 10


def test_cancel_booking_turns_a_storage_failure_into_cancellation_error(conn):
    storage.add_booking(conn, booking())
    storage.add_seat_allocation(conn, "PNR1001", "12627", TRAVEL, "3AC", 14)
    conn.execute("CREATE TRIGGER block_delete BEFORE DELETE ON seat_allocations "
                 "BEGIN SELECT RAISE(ABORT, 'simulated failure'); END")
    with pytest.raises(CancellationError):
        cancel_booking(conn, "PNR1001", now=EARLY)
    assert storage.get_booking(conn, "PNR1001").status == "CONFIRMED"

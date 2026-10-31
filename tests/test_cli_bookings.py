from datetime import date

import pytest

from railway import storage
from railway.models import Booking, Traveller
from railway.registration import register_passenger

DAY = date(2026, 11, 2)
LOGIN_DEMO = ["2", "demo@railway.com", "demo12345"]


def add_booking(conn, pnr="PNR1001", email="demo@railway.com", fare=3000.0, **kw):
    fields = dict(pnr=pnr, passenger_email=email, train_number="12627",
                  travel_date=DAY, seat_class="3AC", passengers=2, fare=fare)
    fields.update(kw)
    storage.add_booking(conn, Booking(**fields),
                        [Traveller("Asha", 30, "F"), Traveller("Ravi", 8, "M")])
    storage.add_seat_allocation(conn, pnr, "12627", DAY, "3AC", 14)
    storage.add_seat_allocation(conn, pnr, "12627", DAY, "3AC", 15)
    storage.set_availability(conn, "12627", DAY, "3AC", 58)


def add_other_user(conn):
    passengers = storage.load_passengers(conn)
    storage.add_passenger(conn, register_passenger("Bina", "bina@x.com", "binapass1", passengers))


# ------------------------------------------------------------ booking (FR-04)

BOOK_INPUTS = ["6", "12627", "2026-11-02", "3ac", "2",
               "Asha", "30", "F", "Ravi", "8", "M"]


def test_booking_collects_details_and_calls_the_booking_function(run_cli):
    calls = []

    def fake_book(conn, email, train_number, day, seat_class, travellers):
        calls.append((email, train_number, day, seat_class, travellers))
        return type("Result", (), {"pnr": "PNR7777"})()

    out = run_cli(LOGIN_DEMO + BOOK_INPUTS + ["0"], book=fake_book)
    assert "Booking confirmed. PNR: PNR7777" in out
    assert calls == [("demo@railway.com", "12627", DAY, "3AC",
                      [Traveller("Asha", 30, "F"), Traveller("Ravi", 8, "M")])]


def test_booking_errors_from_the_booking_function_are_shown(run_cli):
    def failing(*args):
        raise ValueError("No seats left.")

    out = run_cli(LOGIN_DEMO + BOOK_INPUTS + ["0"], book=failing)
    assert "Error: No seats left." in out
    assert "Booking confirmed" not in out


def test_booking_needs_login_even_when_booking_exists(run_cli):
    assert "Error: Not logged in." in run_cli(["6", "0"], book=lambda *a: None)


def test_booking_reports_when_fr04_is_not_merged(run_cli, monkeypatch):
    monkeypatch.setattr("railway.cli._load_booking_function", lambda: None)
    out = run_cli(LOGIN_DEMO + ["6", "0"])
    assert "Booking is not available yet" in out


@pytest.mark.parametrize("count,message", [
    ("0", "Passengers must be between 1 and 6."),
    ("7", "Passengers must be between 1 and 6."),
    ("two", "Number of passengers must be a whole number."),
])
def test_passenger_count_is_checked_before_asking_for_details(run_cli, count, message):
    out = run_cli(LOGIN_DEMO + ["6", "12627", "2026-11-02", "SL", count, "0"],
                  book=lambda *a: None)
    assert f"Error: {message}" in out


def test_non_numeric_age_is_rejected(run_cli):
    out = run_cli(LOGIN_DEMO + ["6", "12627", "2026-11-02", "SL", "1", "Asha", "abc", "0"],
                  book=lambda *a: None)
    assert "Error: Age must be a whole number." in out


# --------------------------------------------------------- viewing bookings

def test_my_bookings_lists_only_my_own(run_cli, cli_conn):
    add_other_user(cli_conn)
    add_booking(cli_conn, "PNR1001")
    storage.add_booking(cli_conn, Booking("PNR2002", "bina@x.com", "12627", DAY, "SL", 1, 600.0),
                        [Traveller("Bina", 25, "F")])
    out = run_cli(LOGIN_DEMO + ["7", "0"])
    assert "PNR1001" in out and "CONFIRMED" in out
    assert "PNR2002" not in out


def test_my_bookings_when_empty(run_cli):
    assert "You have no bookings yet." in run_cli(LOGIN_DEMO + ["7", "0"])


def test_view_booking_shows_travellers_and_seats(run_cli, cli_conn):
    add_booking(cli_conn)
    out = run_cli(LOGIN_DEMO + ["8", "PNR1001", "0"])
    assert "PNR PNR1001   Status: CONFIRMED" in out
    assert "Asha, 30, F" in out and "Ravi, 8, M" in out
    assert "Seats: 14, 15" in out


def test_other_passengers_booking_is_hidden(run_cli, cli_conn):
    add_other_user(cli_conn)
    add_booking(cli_conn, email="bina@x.com")
    out = run_cli(LOGIN_DEMO + ["8", "PNR1001", "0"])
    assert "Error: No booking found for PNR PNR1001." in out
    assert "Asha" not in out


def test_unknown_or_blank_pnr(run_cli):
    out = run_cli(LOGIN_DEMO + ["8", "NOPE", "8", "", "0"])
    assert "Error: No booking found for PNR NOPE." in out
    assert "Error: No booking found for PNR (blank)." in out


# ------------------------------------------------------------- cancellation

def test_cancel_shows_refund_then_cancels_on_yes(run_cli, cli_conn):
    add_booking(cli_conn)
    out = run_cli(LOGIN_DEMO + ["9", "PNR1001", "y", "0"])
    assert "Refund if you cancel now: Rs 2700.00" in out      # 10% fee
    assert "Booking PNR1001 cancelled. 2 seat(s) released. Refund: Rs 2700.00" in out
    assert storage.get_booking(cli_conn, "PNR1001").status == "CANCELLED"
    assert storage.get_availability(cli_conn, "12627", DAY, "3AC") == 60
    assert storage.get_seat_numbers(cli_conn, "PNR1001") == []


def test_cancel_declined_changes_nothing(run_cli, cli_conn):
    add_booking(cli_conn)
    out = run_cli(LOGIN_DEMO + ["9", "PNR1001", "n", "0"])
    assert "Booking not cancelled." in out
    assert storage.get_booking(cli_conn, "PNR1001").status == "CONFIRMED"
    assert storage.get_availability(cli_conn, "12627", DAY, "3AC") == 58


def test_cancel_inside_four_hours_is_refused(run_cli, cli_conn):
    from datetime import datetime
    add_booking(cli_conn)
    out = run_cli(LOGIN_DEMO + ["9", "PNR1001", "0"], now=datetime(2026, 11, 2, 16, 0))
    assert "Error: Cancellation is allowed only up to 4 hours before departure." in out
    assert storage.get_booking(cli_conn, "PNR1001").status == "CONFIRMED"


def test_cancel_between_4_and_24_hours_costs_half(run_cli, cli_conn):
    from datetime import datetime
    add_booking(cli_conn)
    out = run_cli(LOGIN_DEMO + ["9", "PNR1001", "n", "0"], now=datetime(2026, 11, 2, 10, 0))
    assert "Refund if you cancel now: Rs 1500.00" in out


def test_cancelling_twice_is_refused(run_cli, cli_conn):
    add_booking(cli_conn)
    out = run_cli(LOGIN_DEMO + ["9", "PNR1001", "y", "9", "PNR1001", "0"])
    assert "Error: Booking PNR1001 is already cancelled." in out


def test_cannot_cancel_someone_elses_booking(run_cli, cli_conn):
    add_other_user(cli_conn)
    add_booking(cli_conn, email="bina@x.com")
    out = run_cli(LOGIN_DEMO + ["9", "PNR1001", "0"])
    assert "Error: No booking found for PNR PNR1001." in out
    assert storage.get_booking(cli_conn, "PNR1001").status == "CONFIRMED"


def test_bad_name_of_second_passenger_is_reported_straight_away(run_cli):
    calls = []
    out = run_cli(LOGIN_DEMO + ["6", "12627", "2026-11-02", "SL", "2",
                                "Asha Rao", "30", "F", "As@ha", "20", "M", "0"],
                  book=lambda *a: calls.append(a))
    assert "Error: Passenger 2: name can only contain letters" in out
    assert calls == []          # nothing was booked


def test_bad_gender_is_reported_with_passenger_number(run_cli):
    out = run_cli(LOGIN_DEMO + ["6", "12627", "2026-11-02", "SL", "1",
                                "Asha Rao", "30", "robot", "0"],
                  book=lambda *a: None)
    assert "Error: Passenger 1: gender must be M, F or O." in out


def test_valid_passengers_are_passed_on_cleaned(run_cli):
    calls = []
    run_cli(LOGIN_DEMO + ["6", "12627", "2026-11-02", "SL", "1",
                          "Asha   Rao ", "30", "female", "0"],
            book=lambda *a: calls.append(a) or "PNR1")
    travellers = calls[0][-1]
    assert [(t.name, t.age, t.gender) for t in travellers] == [("Asha Rao", 30, "F")]
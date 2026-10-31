
from railway import storage
from datetime import date

from railway.models import Booking, CONFIRMED, Passenger, ROLE_ADMIN


def add_admin(conn):
    """Create a test administrator account."""
    storage.add_passenger(
        conn,
        Passenger(
            email="admin@railway.com",
            name="Admin",
            password_hash="test$adminpass1",
            role=ROLE_ADMIN,
        ),
    )


def test_admin_can_add_train_and_it_appears_in_search(
    cli_conn,
    run_cli,
):
    add_admin(cli_conn)

    output = run_cli([
        "2",
        "admin@railway.com",
        "adminpass1",
        "10",
        "99999",
        "Test Express",
        "Bengaluru",
        "Chennai",
        "09:30",
        "0,1,2,3,4,5,6",
        "SL",
        "100",
        "250",
        "4",
        "Bengaluru",
        "Chennai",
        "2026-11-02",
        "0",
    ])

    assert "Train 99999 added successfully." in output
    assert "99999" in output
    assert "Test Express" in output
    assert "Bengaluru -> Chennai" in output
    assert "SL" in output
    assert "250.00" in output


def test_duplicate_train_number_is_rejected(
    cli_conn,
    run_cli,
):
    add_admin(cli_conn)

    output = run_cli([
        "2",
        "admin@railway.com",
        "adminpass1",
        "10",
        "12627",
        "Duplicate Express",
        "Bengaluru",
        "Chennai",
        "09:30",
        "0,1,2,3,4,5,6",
        "SL",
        "100",
        "250",
        "0",
    ])

    assert "Train number 12627 already exists." in output
    assert storage.get_train(cli_conn, "12627").name == (
        "Karnataka Express"
    )


def test_missing_required_train_name_is_rejected(
    cli_conn,
    run_cli,
):
    add_admin(cli_conn)

    output = run_cli([
        "2",
        "admin@railway.com",
        "adminpass1",
        "10",
        "99998",
        "",
        "Bengaluru",
        "Chennai",
        "09:30",
        "0,1,2,3,4,5,6",
        "SL",
        "100",
        "250",
        "0",
    ])

    assert "Train name is required." in output
    assert storage.get_train(cli_conn, "99998") is None


def test_passenger_cannot_add_train(cli_conn, run_cli):
    output = run_cli([
        "2",
        "demo@railway.com",
        "demo12345",
        "10",
        "0",
    ])

    assert "Admin access required." in output
    assert storage.get_train(cli_conn, "99999") is None


def test_logged_out_user_cannot_add_train(run_cli):
    output = run_cli([
        "10",
        "0",
    ])

    assert "Not logged in" in output or "login" in output.lower()


# FR-14: Admin update and remove train

def test_admin_can_update_train(cli_conn, run_cli):
    add_admin(cli_conn)

    output = run_cli([
        "2", "admin@railway.com", "adminpass1",
        "11", "12627",
        "Updated Karnataka Express",
        "", "", "10:15", "",
        "0",
    ])

    updated = storage.get_train(cli_conn, "12627")
    assert "updated successfully" in output.lower()
    assert updated.name == "Updated Karnataka Express"
    assert updated.departure == "10:15"


def test_admin_can_remove_train_without_confirmed_bookings(cli_conn, run_cli):
    add_admin(cli_conn)

    output = run_cli([
        "2", "admin@railway.com", "adminpass1",
        "12", "12627", "Y",
        "0",
    ])

    assert "removed successfully" in output.lower()
    assert all(t.number != "12627" for t in storage.list_trains(cli_conn))


def test_admin_cannot_remove_train_with_confirmed_booking(cli_conn):
    booking = Booking(
        "TESTPNR001",
        "demo@railway.com",
        "12627",
        date(2026, 11, 2),
        "SL",
        1,
        250.0,
        CONFIRMED,
    )
    storage.add_booking(cli_conn, booking)

    try:
        storage.remove_train(cli_conn, "12627")
        assert False, "Expected removal to be blocked"
    except storage.StorageError as exc:
        assert "active bookings" in str(exc).lower()

    assert any(t.number == "12627" for t in storage.list_trains(cli_conn))


def test_passenger_cannot_update_or_remove_train(cli_conn, run_cli):
    output = run_cli([
        "2", "demo@railway.com", "demo12345",
        "11", "12627",
        "12", "12627", "Y",
        "0",
    ])

    assert output.count("Admin access required.") >= 2
    assert any(t.number == "12627" for t in storage.list_trains(cli_conn))


def test_logged_out_user_cannot_update_or_remove_train(run_cli):
    output = run_cli([
        "11", "12", "0",
    ])

    assert "Not logged in" in output or "login" in output.lower()

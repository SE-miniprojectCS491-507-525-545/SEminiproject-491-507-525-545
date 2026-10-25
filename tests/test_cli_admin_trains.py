
from railway import storage
from railway.models import Passenger, ROLE_ADMIN


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

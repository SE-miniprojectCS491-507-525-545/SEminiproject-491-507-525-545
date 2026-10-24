from datetime import date

from railway import storage

DAY = "2026-11-02"


def test_search_lists_trains_with_fares_and_free_seats(run_cli):
    out = run_cli(["4", "bengaluru", "DELHI", DAY, "0"])
    assert "1 train(s) found on 2026-11-02" in out
    assert "12627  Karnataka Express" in out
    assert "3AC" in out and "1500.00" in out and "60 seats free" in out
    assert "SL" in out and "120 seats free" in out


def test_search_shows_every_train_on_a_route(run_cli):
    out = run_cli(["4", "Bengaluru", "Mysuru", DAY, "0"])
    assert "20601  Bengaluru-Mysuru Intercity" in out


def test_search_with_no_service_says_so(run_cli):
    out = run_cli(["4", "Mysuru", "Delhi", DAY, "0"])
    assert "No trains found for that route and date." in out


def test_search_errors_are_shown_not_raised(run_cli):
    assert "Error: Unknown station: Atlantis." in run_cli(["4", "Atlantis", "Delhi", DAY, "0"])
    assert "Error: Source and destination cannot be the same." in run_cli(["4", "Delhi", "delhi", DAY, "0"])
    assert "Error: Travel date cannot be in the past." in run_cli(["4", "Bengaluru", "Delhi", "2026-10-01", "0"])
    assert "Error: Travel date must be in YYYY-MM-DD format." in run_cli(["4", "Bengaluru", "Delhi", "02/11/2026", "0"])
    assert "Error: Source station is required." in run_cli(["4", "", "Delhi", DAY, "0"])
    assert "Error: Travel date is required." in run_cli(["4", "Bengaluru", "Delhi", "", "0"])


def test_search_shows_sold_out_classes(run_cli, cli_conn):
    storage.set_availability(cli_conn, "12627", date(2026, 11, 2), "3AC", 0)
    out = run_cli(["4", "Bengaluru", "Delhi", DAY, "0"])
    assert "SOLD OUT" in out
    assert "120 seats free" in out


def test_check_seats_lists_all_classes(run_cli, cli_conn):
    storage.set_availability(cli_conn, "12627", date(2026, 11, 2), "SL", 7)
    out = run_cli(["5", "12627", DAY, "0"])
    assert "7 seats free" in out
    assert "60 seats free" in out


def test_check_seats_unknown_train(run_cli):
    assert "Error: Train 99999 not found" in run_cli(["5", "99999", DAY, "0"])


def test_check_seats_past_date(run_cli):
    assert "Error: Travel date cannot be in the past" in run_cli(["5", "12627", "2026-10-01", "0"])
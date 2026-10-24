from railway import storage


def test_exit_says_goodbye(run_cli):
    assert "Goodbye." in run_cli(["0"])


def test_invalid_menu_choice_is_reported(run_cli):
    out = run_cli(["42", "", "0"])
    assert out.count("Invalid choice") == 2


def test_register_login_logout_flow(run_cli, cli_conn):
    out = run_cli([
        "1", "Asha", "asha@x.com", "pass1234",
        "2", "asha@x.com", "pass1234",
        "3", "0",
    ])
    assert "Registered Asha" in out
    assert "Logged in as Asha." in out
    assert "Logged out." in out
    stored = storage.get_passenger(cli_conn, "asha@x.com")
    assert stored.name == "Asha"
    assert stored.password_hash != "pass1234"


def test_status_line_follows_login_state(run_cli):
    out = run_cli(["2", "demo@railway.com", "demo12345", "0"])
    assert "Not logged in" in out
    assert out.rstrip().splitlines()[-2] == "Logged in as Demo User"


def test_weak_password_is_rejected_with_a_message(run_cli, cli_conn):
    out = run_cli(["1", "Asha", "asha@x.com", "short1", "0"])
    assert "Error: Password must be at least 8 characters." in out
    assert storage.get_passenger(cli_conn, "asha@x.com") is None


def test_duplicate_registration_is_rejected(run_cli):
    out = run_cli(["1", "Demo", "demo@railway.com", "demo12345", "0"])
    assert "Error: An account with this email already exists." in out


def test_wrong_password_does_not_log_in(run_cli):
    out = run_cli(["2", "demo@railway.com", "wrongpass1", "0"])
    assert "Error: Invalid email or password." in out
    assert out.rstrip().splitlines()[-2] == "Not logged in"


def test_logout_without_login_is_an_error(run_cli):
    assert "Error: Not logged in." in run_cli(["3", "0"])


def test_account_actions_need_login(run_cli):
    out = run_cli(["6", "7", "8", "9", "0"])
    assert out.count("Error: Not logged in.") == 4
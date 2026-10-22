import pytest

from railway.auth import AuthError, current_passenger, login, logout
from railway.registration import register_passenger


@pytest.fixture
def passengers():
    accounts = {}
    register_passenger("Asha Rao", "asha@example.com", "Secret123", accounts)
    return accounts


def test_login_with_correct_credentials_returns_token(passengers):
    sessions = {}
    token = login("asha@example.com", "Secret123", passengers, sessions)
    assert token
    assert sessions[token] == "asha@example.com"


def test_login_trims_and_ignores_case_of_email(passengers):
    sessions = {}
    token = login("  ASHA@Example.com ", "Secret123", passengers, sessions)
    assert sessions[token] == "asha@example.com"


def test_wrong_password_is_refused(passengers):
    with pytest.raises(AuthError, match="Invalid email or password"):
        login("asha@example.com", "Wrong1234", passengers, {})


def test_unknown_email_is_refused(passengers):
    with pytest.raises(AuthError, match="Invalid email or password"):
        login("nobody@example.com", "Secret123", passengers, {})


def test_wrong_password_and_unknown_email_give_same_message(passengers):
    with pytest.raises(AuthError) as wrong_password:
        login("asha@example.com", "Wrong1234", passengers, {})
    with pytest.raises(AuthError) as unknown_email:
        login("nobody@example.com", "Secret123", passengers, {})
    assert str(wrong_password.value) == str(unknown_email.value)


@pytest.mark.parametrize(
    "email,password,message",
    [
        ("", "Secret123", "Email is required"),
        ("   ", "Secret123", "Email is required"),
        (None, "Secret123", "Email is required"),
        ("asha@example.com", "", "Password is required"),
        ("asha@example.com", None, "Password is required"),
    ],
)
def test_missing_input_is_rejected(email, password, message, passengers):
    with pytest.raises(AuthError, match=message):
        login(email, password, passengers, {})


def test_failed_login_creates_no_session(passengers):
    sessions = {}
    with pytest.raises(AuthError):
        login("asha@example.com", "Wrong1234", passengers, sessions)
    assert sessions == {}


def test_each_login_gets_a_different_token(passengers):
    sessions = {}
    first = login("asha@example.com", "Secret123", passengers, sessions)
    second = login("asha@example.com", "Secret123", passengers, sessions)
    assert first != second


def test_logout_ends_the_session(passengers):
    sessions = {}
    token = login("asha@example.com", "Secret123", passengers, sessions)
    logout(token, sessions)
    assert token not in sessions


@pytest.mark.parametrize("token", ["not-a-real-token", None])
def test_logout_when_not_logged_in_is_refused(token):
    with pytest.raises(AuthError, match="Not logged in"):
        logout(token, {})


def test_logout_twice_is_refused(passengers):
    sessions = {}
    token = login("asha@example.com", "Secret123", passengers, sessions)
    logout(token, sessions)
    with pytest.raises(AuthError, match="Not logged in"):
        logout(token, sessions)


def test_current_passenger_returns_logged_in_account(passengers):
    sessions = {}
    token = login("asha@example.com", "Secret123", passengers, sessions)
    assert current_passenger(token, passengers, sessions) is passengers["asha@example.com"]


def test_current_passenger_after_logout_is_refused(passengers):
    sessions = {}
    token = login("asha@example.com", "Secret123", passengers, sessions)
    logout(token, sessions)
    with pytest.raises(AuthError, match="Not logged in"):
        current_passenger(token, passengers, sessions)


def test_current_passenger_with_unknown_token_is_refused(passengers):
    with pytest.raises(AuthError, match="Not logged in"):
        current_passenger("not-a-real-token", passengers, {})

def test_session_for_a_deleted_account_gives_auth_error_not_key_error():
    sessions = {"tok": "ghost@example.com"}
    with pytest.raises(AuthError):
        current_passenger("tok", {}, sessions)

import pytest

from railway.registration import RegistrationError, register_passenger
from railway.security import verify_password


def test_valid_registration_creates_account():
    passengers = {}
    passenger = register_passenger("Asha Rao", "asha@example.com", "Secret123", passengers)
    assert passengers["asha@example.com"] is passenger
    assert passenger.name == "Asha Rao"


def test_email_is_trimmed_and_lowercased():
    passengers = {}
    register_passenger("Asha", "  ASHA@Example.com ", "Secret123", passengers)
    assert "asha@example.com" in passengers


def test_password_is_stored_hashed_not_plain():
    passenger = register_passenger("Asha", "asha@example.com", "Secret123", {})
    assert passenger.password_hash != "Secret123"
    assert "Secret123" not in passenger.password_hash
    assert verify_password("Secret123", passenger.password_hash)


@pytest.mark.parametrize(
    "name,email,password,message",
    [
        ("", "a@b.com", "Secret123", "Name is required"),
        ("   ", "a@b.com", "Secret123", "Name is required"),
        (None, "a@b.com", "Secret123", "Name is required"),
        ("Asha", "", "Secret123", "Email is required"),
        ("Asha", "a@b.com", "", "Password is required"),
        ("Asha", "not-an-email", "Secret123", "Email is not valid"),
        ("Asha", "a@b.com", "short1", "at least 8"),
        ("Asha", "a@b.com", "onlyletters", "letter and one digit"),
        ("Asha", "a@b.com", "12345678", "letter and one digit"),
    ],
)
def test_invalid_registration_is_rejected(name, email, password, message):
    with pytest.raises(RegistrationError, match=message):
        register_passenger(name, email, password, {})


def test_duplicate_email_is_rejected_even_with_different_case():
    passengers = {}
    register_passenger("Asha", "asha@example.com", "Secret123", passengers)
    with pytest.raises(RegistrationError, match="already exists"):
        register_passenger("Asha Two", "ASHA@example.com", "Another123", passengers)
    assert len(passengers) == 1


def test_failed_registration_stores_nothing():
    passengers = {}
    with pytest.raises(RegistrationError):
        register_passenger("Asha", "bad-email", "Secret123", passengers)
    assert passengers == {}
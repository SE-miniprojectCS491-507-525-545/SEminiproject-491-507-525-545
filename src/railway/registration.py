import re
from dataclasses import dataclass

from railway.security import hash_password

MIN_PASSWORD_LENGTH = 8
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegistrationError(ValueError):
    """Raised when passenger registration input is invalid."""


@dataclass(frozen=True)
class Passenger:
    email: str
    name: str
    password_hash: str


def _clean(value):
    return (value or "").strip()


def validate_registration(name, email, password, passengers):
    """Validate registration input (FR-09). Returns cleaned (name, email)."""
    name = _clean(name)
    email = _clean(email).lower()

    if not name:
        raise RegistrationError("Name is required.")
    if not email:
        raise RegistrationError("Email is required.")
    if not password:
        raise RegistrationError("Password is required.")
    if not EMAIL_PATTERN.match(email):
        raise RegistrationError("Email is not valid.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise RegistrationError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        )
    if not (any(c.isalpha() for c in password) and any(c.isdigit() for c in password)):
        raise RegistrationError("Password must contain at least one letter and one digit.")
    if email in passengers:
        raise RegistrationError("An account with this email already exists.")
    return name, email


def register_passenger(name, email, password, passengers):
    """Create a passenger account (FR-09).

    `passengers` maps email -> Passenger. The password is stored only as a
    salted hash (SR-01), never as plain text.
    """
    name, email = validate_registration(name, email, password, passengers)
    passenger = Passenger(email, name, hash_password(password))
    passengers[email] = passenger
    return passenger
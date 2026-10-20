import secrets

from railway.security import verify_password


class AuthError(ValueError):
    """Raised when login or logout fails."""


def _clean(value):
    return (value or "").strip()


def login(email, password, passengers, sessions):
    """Log a passenger in (FR-10). Returns a session token.

    `passengers` maps email -> Passenger (see registration.py).
    `sessions` maps token -> email for everyone currently logged in.
    """
    email = _clean(email).lower()

    if not email:
        raise AuthError("Email is required.")
    if not password:
        raise AuthError("Password is required.")

    passenger = passengers.get(email)
    if passenger is None or not verify_password(password, passenger.password_hash):
        raise AuthError("Invalid email or password.")

    token = secrets.token_hex(16)
    sessions[token] = email
    return token


def logout(token, sessions):
    """Log a passenger out (FR-10)."""
    if token not in sessions:
        raise AuthError("Not logged in.")
    del sessions[token]


def current_passenger(token, passengers, sessions):
    """Return the logged-in Passenger for a token, or raise AuthError."""
    email = sessions.get(token)
    if email is None:
        raise AuthError("Not logged in.")
    return passengers[email]
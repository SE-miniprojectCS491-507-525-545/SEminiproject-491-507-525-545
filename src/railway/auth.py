"""In-memory authentication sessions with configurable expiration."""
import os
import secrets
import time

from railway.security import verify_password

DEFAULT_SESSION_TTL_SECONDS = 30 * 60


class AuthError(ValueError):
    """Raised when login or logout fails."""


class SessionStore(dict):
    """Email-compatible session mapping with separate creation timestamps."""

    def __init__(self):
        super().__init__()
        self.created_at = {}


def _session_ttl():
    raw = os.environ.get("RAILWAY_SESSION_TTL_SECONDS", DEFAULT_SESSION_TTL_SECONDS)
    try:
        ttl = int(raw)
    except (TypeError, ValueError):
        raise AuthError("Session timeout configuration must be a positive integer.") from None
    if ttl <= 0:
        raise AuthError("Session timeout configuration must be a positive integer.")
    return ttl


def _clean(value):
    return (value or "").strip()


def login(email, password, passengers, sessions):
    """Log a passenger in (FR-10). Returns a session token."""
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
    if isinstance(sessions, SessionStore):
        sessions.created_at[token] = time.monotonic()
    return token


def logout(token, sessions):
    """Log a passenger out (FR-10)."""
    if token not in sessions:
        raise AuthError("Not logged in.")
    del sessions[token]
    if isinstance(sessions, SessionStore):
        sessions.created_at.pop(token, None)


def current_passenger(token, passengers, sessions):
    """Return the logged-in Passenger for a valid, non-expired token."""
    email = sessions.get(token)
    if email is None:
        raise AuthError("Not logged in.")

    if isinstance(sessions, SessionStore):
        created = sessions.created_at.get(token)
        if created is None or time.monotonic() - created >= _session_ttl():
            sessions.pop(token, None)
            sessions.created_at.pop(token, None)
            raise AuthError("Session expired. Please log in again.")

    passenger = passengers.get(email)
    if passenger is None:
        raise AuthError("Not logged in.")
    return passenger

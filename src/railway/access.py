from railway.models import ROLE_ADMIN


class AccessError(ValueError):
    """Raised when a user is not allowed to do something (SR-02)."""


def is_admin(passenger):
    return passenger is not None and passenger.role == ROLE_ADMIN


def require_admin(passenger):
    """Only admins may do admin actions (SR-02). Returns the passenger."""
    if passenger is None:
        raise AccessError("Not logged in.")
    if passenger.role != ROLE_ADMIN:
        raise AccessError("Admin access required.")
    return passenger


def can_access_booking(passenger, booking):
    """A passenger may access their own bookings, an admin may access any (SR-02)."""
    if passenger is None or booking is None:
        return False
    if passenger.role == ROLE_ADMIN:
        return True
    return booking.passenger_email.lower() == passenger.email.lower()


def require_booking_access(passenger, booking):
    """Raise AccessError unless the passenger may access this booking."""
    if passenger is None:
        raise AccessError("Not logged in.")
    if not can_access_booking(passenger, booking):
        raise AccessError("You can only access your own bookings.")
    return booking
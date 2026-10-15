CANCELLED = "CANCELLED"


class CancellationError(ValueError):
    """Raised when a cancellation request is invalid."""


def _clean(value):
    return (value or "").strip()


def validate_cancellation(pnr, bookings):
    """Validate a cancellation request (FR-08). Returns the booking to cancel.

    `bookings` maps PNR -> booking object that has a `status` attribute.
    """
    pnr = _clean(pnr)

    if not pnr:
        raise CancellationError("PNR is required.")

    booking = bookings.get(pnr)
    if booking is None:
        raise CancellationError(f"No booking found for PNR {pnr}.")
    if booking.status == CANCELLED:
        raise CancellationError(f"Booking {pnr} is already cancelled.")
    return booking
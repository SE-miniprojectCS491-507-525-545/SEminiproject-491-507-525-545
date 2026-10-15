from dataclasses import dataclass

CANCELLED = "CANCELLED"


class CancellationError(ValueError):
    """Raised when a cancellation request is invalid."""


@dataclass(frozen=True)
class CancellationResult:
    pnr: str
    seats_released: int
    refund_amount: float = 0.0  # calculated in FR-07


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


def cancel_ticket(pnr, bookings, availability, refund_amount=0.0):
    """Cancel a confirmed booking and release its seats (FR-06).

    `availability` maps (train_number, travel_date, seat_class) -> free seats.
    """
    booking = validate_cancellation(pnr, bookings)

    booking.status = CANCELLED
    key = (booking.train_number, booking.travel_date, booking.seat_class)
    availability[key] = availability.get(key, 0) + booking.passengers

    return CancellationResult(_clean(pnr), booking.passengers, refund_amount)
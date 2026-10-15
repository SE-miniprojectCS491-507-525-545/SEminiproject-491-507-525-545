from dataclasses import dataclass
from datetime import datetime, timedelta

CANCELLED = "CANCELLED"
MIN_HOURS_BEFORE_DEPARTURE = 4  # BR-02


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


def departure_datetime(travel_date, departure):
    """Combine a travel date with a 'HH:MM' departure time."""
    hours, minutes = departure.split(":")
    return datetime(
        travel_date.year, travel_date.month, travel_date.day,
        int(hours), int(minutes),
    )


def validate_deadline(travel_date, departure, now=None):
    """Allow cancellation only up to 4 hours before departure (BR-02)."""
    now = now or datetime.now()
    time_left = departure_datetime(travel_date, departure) - now
    if time_left < timedelta(hours=MIN_HOURS_BEFORE_DEPARTURE):
        raise CancellationError(
            f"Cancellation is allowed only up to "
            f"{MIN_HOURS_BEFORE_DEPARTURE} hours before departure."
        )


def cancel_ticket(pnr, bookings, availability, trains, now=None, refund_amount=0.0):
    """Cancel a confirmed booking and release its seats (FR-06, BR-02).

    `availability` maps (train_number, travel_date, seat_class) -> free seats.
    `trains` is the list of Train objects, used to find the departure time.
    """
    booking = validate_cancellation(pnr, bookings)

    train = next((t for t in trains if t.number == booking.train_number), None)
    if train is None:
        raise CancellationError(f"Train {booking.train_number} not found.")
    validate_deadline(booking.travel_date, train.departure, now)

    booking.status = CANCELLED
    key = (booking.train_number, booking.travel_date, booking.seat_class)
    availability[key] = availability.get(key, 0) + booking.passengers

    return CancellationResult(_clean(pnr), booking.passengers, refund_amount)
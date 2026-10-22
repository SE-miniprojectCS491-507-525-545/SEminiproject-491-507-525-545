from dataclasses import dataclass
from datetime import datetime, timedelta

from railway import storage

CANCELLED = "CANCELLED"
MIN_HOURS_BEFORE_DEPARTURE = 4  # BR-02
FEE_RATE_MORE_THAN_24H = 0.10  # FR-07: more than 24 hours before departure
FEE_RATE_4_TO_24H = 0.50  # FR-07: from 24 hours down to 4 hours before


class CancellationError(ValueError):
    """Raised when a cancellation request is invalid."""


@dataclass(frozen=True)
class CancellationResult:
    pnr: str
    seats_released: int
    refund_amount: float = 0.0


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


def calculate_refund(fare, travel_date, departure, now=None):
    """Refund = fare minus a cancellation fee (FR-07).

    More than 24 hours before departure: 10% fee. From 24 hours down: 50% fee.
    No refund once the train has departed. (Cancelling inside the last
    4 hours is refused separately by validate_deadline, BR-02.)
    """
    now = now or datetime.now()
    time_left = departure_datetime(travel_date, departure) - now
    if time_left <= timedelta(0):
        return 0.0
    if time_left > timedelta(hours=24):
        fee_rate = FEE_RATE_MORE_THAN_24H
    else:
        fee_rate = FEE_RATE_4_TO_24H
    return round(fare - fare * fee_rate, 2)


def _find_train(booking, trains):
    train = next((t for t in trains if t.number == booking.train_number), None)
    if train is None:
        raise CancellationError(f"Train {booking.train_number} not found.")
    return train


def preview_refund(pnr, bookings, trains, now=None):
    """Show the refund before the cancellation is final (FR-07). Changes nothing."""
    booking = validate_cancellation(pnr, bookings)
    train = _find_train(booking, trains)
    validate_deadline(booking.travel_date, train.departure, now)
    return calculate_refund(booking.fare, booking.travel_date, train.departure, now)


def cancel_ticket(pnr, bookings, availability, trains, now=None):
    """Cancel a confirmed booking, release its seats and work out the refund.

    `availability` maps (train_number, travel_date, seat_class) -> free seats.
    `trains` is the list of Train objects, used to find the departure time.
    """
    booking = validate_cancellation(pnr, bookings)
    train = _find_train(booking, trains)
    validate_deadline(booking.travel_date, train.departure, now)
    refund = calculate_refund(booking.fare, booking.travel_date, train.departure, now)

    booking.status = CANCELLED
    key = (booking.train_number, booking.travel_date, booking.seat_class)
    availability[key] = availability.get(key, 0) + booking.passengers

    return CancellationResult(_clean(pnr), booking.passengers, refund)


def cancel_booking(conn, pnr, now=None):
    """Database version of cancel_ticket (FR-06, FR-07, BR-02, NFR-04).

    Checks the PNR, the 4-hour deadline and the refund, then updates the
    booking status, the free-seat count and the seat numbers together in one
    step, so a failure part-way leaves nothing half-changed.
    """
    pnr = _clean(pnr)
    found = storage.get_booking(conn, pnr) if pnr else None
    booking = validate_cancellation(pnr, {pnr: found} if found else {})
    train = storage.get_train(conn, booking.train_number)
    if train is None:
        raise CancellationError(f"Train {booking.train_number} not found.")
    validate_deadline(booking.travel_date, train.departure, now)
    refund = calculate_refund(booking.fare, booking.travel_date, train.departure, now)
    try:
        released = storage.apply_cancellation(conn, pnr)
    except storage.StorageError as exc:
        raise CancellationError(str(exc)) from exc
    return CancellationResult(pnr, released, refund)

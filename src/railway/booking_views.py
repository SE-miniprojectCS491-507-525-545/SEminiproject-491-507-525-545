"""View bookings (FR-11, FR-15), using the access rules from access.py (SR-02).

    details = view_booking(conn, "PNR1001", passenger)      # FR-11
    print(format_booking_details(details))

    bookings = list_all_bookings(conn, admin_passenger)     # FR-15
    print(format_booking_list(bookings))
"""
from dataclasses import dataclass

from railway import storage
from railway.access import AccessError, can_access_booking, require_admin


class BookingViewError(ValueError):
    """Raised when a booking cannot be shown. The message is user-facing."""


@dataclass(frozen=True)
class BookingDetails:
    booking: object
    train_name: str
    travellers: tuple
    seat_numbers: tuple


def _clean(value):
    return (value or "").strip()


def view_booking(conn, pnr, passenger):
    """Show one booking by PNR (FR-11).

    Passengers can view only their own bookings; admins can view any (SR-02).
    Someone else's PNR gets the same "not found" answer as a PNR that does not
    exist, so PNRs cannot be guessed.
    """
    if passenger is None:
        raise AccessError("Not logged in.")
    pnr = _clean(pnr)
    if not pnr:
        raise BookingViewError("PNR is required.")

    booking = storage.get_booking(conn, pnr)
    if booking is None or not can_access_booking(passenger, booking):
        raise BookingViewError(f"No booking found for PNR {pnr}.")

    train = storage.get_train(conn, booking.train_number)
    return BookingDetails(
        booking=booking,
        train_name=train.name if train else "",
        travellers=tuple(storage.get_travellers(conn, pnr)),
        seat_numbers=tuple(storage.get_seat_numbers(conn, pnr)),
    )


def list_all_bookings(conn, passenger):
    """Every booking in the system, for admins only (FR-15, SR-02)."""
    require_admin(passenger)
    return storage.list_bookings(conn)


def format_booking_details(details):
    """Text shown for one booking: PNR, status, train, date, class, travellers, fare."""
    booking = details.booking
    seats = ", ".join(str(s) for s in details.seat_numbers) or "not allocated"
    lines = [
        f"Booking {booking.pnr}",
        f"Status: {booking.status}",
        f"Train: {booking.train_number} {details.train_name}".rstrip(),
        f"Date: {booking.travel_date.isoformat()}",
        f"Class: {booking.seat_class}",
        "Passengers:",
    ]
    for person in details.travellers:
        lines.append(f"  {person.name}, {person.age}, {person.gender}")
    lines.append(f"Seats: {seats}")
    lines.append(f"Fare: {booking.fare:.2f}")
    return "\n".join(lines)


def format_booking_list(bookings):
    """One line per booking, for the admin list."""
    if not bookings:
        return "No bookings found."
    return "\n".join(
        f"{b.pnr} | {b.passenger_email} | train {b.train_number} | "
        f"{b.travel_date.isoformat()} | {b.seat_class} | "
        f"{b.passengers} seat(s) | {b.status}"
        for b in bookings
    )
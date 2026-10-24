"""Ticket booking (FR-04a).

Typical use, after the passenger has logged in:
    ticket = book_ticket(conn, passenger.email, "12627", "2026-11-02", "3AC",
                         [Traveller("Asha Rao", 30, "F")])
    print(format_ticket(ticket))

Seats are reserved inside the same all-or-nothing database step that saves the
booking (storage.book_seats), so seat counts stay correct even if something
fails part-way, and no separate reserve call is needed.
"""
from dataclasses import dataclass
from datetime import date

from railway import availability, storage
from railway.availability import AvailabilityError
from railway.models import CONFIRMED
from railway.pnr import PNRError, generate_pnr
from railway.traveller_validation import TravellerError, validate_travellers


class BookingError(ValueError):
    """Raised when a booking cannot be made. The message is user-facing."""


@dataclass(frozen=True)
class Ticket:
    pnr: str
    train_number: str
    train_name: str
    travel_date: date
    seat_class: str
    travellers: tuple
    seat_numbers: tuple
    fare: float
    status: str = CONFIRMED


def _no_seats_message(info_class, train_number, day, free, wanted):
    if free == 0:
        return (f"No seats available in {info_class} on train {train_number} "
                f"for {day.isoformat()}.")
    return f"Only {free} seat(s) left in {info_class}; you asked for {wanted}."


def book_ticket(conn, passenger_email, train_number, travel_date, seat_class,
                travellers, today=None):
    """Book seats for a logged-in passenger and return a Ticket."""
    email = (passenger_email or "").strip().lower()
    if not email or storage.get_passenger(conn, email) is None:
        raise BookingError("Please log in with a registered account before booking.")
    try:
        people = validate_travellers(travellers)
        info = availability.check_availability(conn, train_number, travel_date,
                                               seat_class, today)
    except (TravellerError, AvailabilityError) as exc:
        raise BookingError(str(exc)) from exc

    day, wanted = info.travel_date, len(people)
    if wanted > info.free_seats:
        raise BookingError(_no_seats_message(
            info.seat_class, info.train_number, day, info.free_seats, wanted))

    try:
        pnr = generate_pnr(lambda p: storage.get_booking(conn, p) is not None)
        booking, seats = storage.book_seats(
            conn, pnr, email, info.train_number, day, info.seat_class, people)
    except storage.NotEnoughSeats as exc:   # someone else took the seats just now
        raise BookingError(_no_seats_message(
            info.seat_class, info.train_number, day, exc.free, wanted)) from exc
    except (PNRError, storage.StorageError) as exc:
        raise BookingError(str(exc)) from exc

    train = storage.get_train(conn, booking.train_number)
    return Ticket(booking.pnr, booking.train_number, train.name, booking.travel_date,
                  booking.seat_class, tuple(people), tuple(seats), booking.fare,
                  booking.status)


def format_ticket(ticket):
    """Booking confirmation text: PNR, train, date, class, seats and fare."""
    lines = [
        "Booking confirmed",
        f"PNR: {ticket.pnr}",
        f"Train: {ticket.train_number} {ticket.train_name}",
        f"Date: {ticket.travel_date.isoformat()}",
        f"Class: {ticket.seat_class}",
        "Passengers:",
    ]
    for person, seat in zip(ticket.travellers, ticket.seat_numbers):
        lines.append(f"  {person.name}, {person.age}, {person.gender} - seat {seat}")
    lines.append(f"Fare: {ticket.fare:.2f}")
    return "\n".join(lines)

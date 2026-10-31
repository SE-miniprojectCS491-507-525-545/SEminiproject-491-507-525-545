"""Shared data model for the Railway Reservation System (TASK-01).

These plain dataclasses are what every feature module passes around.
Field names match the code that already exists:
  * Train      -> same fields as the Train in search.py (so it can be swapped in)
  * Booking    -> the attributes cancellation.py reads (status, train_number,
                  travel_date, seat_class, passengers, fare)
  * Passenger  -> same fields as the Passenger in registration.py
"""
from dataclasses import dataclass
from datetime import date

CONFIRMED = "CONFIRMED"
CANCELLED = "CANCELLED"  # same value cancellation.py uses

ROLE_PASSENGER = "passenger"
ROLE_ADMIN = "admin"


@dataclass(frozen=True)
class Train:
    number: str
    name: str
    source: str
    destination: str
    departure: str  # "HH:MM"
    runs_on: tuple  # weekdays the train runs, 0 = Monday ... 6 = Sunday


@dataclass(frozen=True)
class SeatClass:
    """One class (e.g. 3AC) on one train: how many seats and the fare."""
    train_number: str
    seat_class: str
    total_seats: int
    fare: float


@dataclass(frozen=True)
class Passenger:
    """A user account. role is 'passenger' or 'admin' (SR-02)."""
    email: str
    name: str
    password_hash: str
    role: str = ROLE_PASSENGER


@dataclass(frozen=True)
class Traveller:
    """One person travelling on a booking (FR-05)."""
    name: str
    age: int
    gender: str


@dataclass
class Booking:
    """A ticket booking. Not frozen: cancel_ticket() changes `status`.

    `passengers` is the NUMBER of travellers (cancellation.py adds it back to
    the free seats). The travellers' details are stored separately.
    """
    pnr: str
    passenger_email: str
    train_number: str
    travel_date: date
    seat_class: str
    passengers: int
    fare: float
    status: str = CONFIRMED
    departure_at_booking: str | None = None

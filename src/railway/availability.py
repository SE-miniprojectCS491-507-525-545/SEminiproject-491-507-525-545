"""Seat availability lookup (FR-02), built on the shared storage layer.

Typical use:
    conn = storage.connect()
    info = check_availability(conn, "12627", "2026-11-02", "3AC")
    print(info.free_seats, info.status)
"""
from dataclasses import dataclass
from datetime import date, datetime

from railway import storage

AVAILABLE = "AVAILABLE"
SOLD_OUT = "SOLD OUT"

_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday")


class AvailabilityError(ValueError):
    """Bad input for an availability check. The message is user-facing."""


@dataclass(frozen=True)
class Availability:
    train_number: str
    travel_date: date
    seat_class: str
    total_seats: int
    free_seats: int
    fare: float

    @property
    def status(self):
        return AVAILABLE if self.free_seats > 0 else SOLD_OUT


def _to_date(value):
    """Accept a date, datetime or 'YYYY-MM-DD' string."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None or not str(value).strip():
        raise AvailabilityError("Travel date is required")
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        raise AvailabilityError(
            "Travel date must be a valid date in YYYY-MM-DD format") from None


def _find_train(conn, train_number):
    number = str(train_number or "").strip()
    train = storage.get_train(conn, number) if number else None
    if train is None:
        raise AvailabilityError(f"Train {number or '(blank)'} not found")
    return train


def _check_day(train, day, today):
    today = today or date.today()
    if day < today:
        raise AvailabilityError("Travel date cannot be in the past")
    if day.weekday() not in train.runs_on:
        raise AvailabilityError(
            f"Train {train.number} does not run on {day.isoformat()} "
            f"({_WEEKDAYS[day.weekday()]})")


def _availability_for(conn, train, day, seat_class):
    # No row recorded yet means nothing has been booked: all seats are free.
    free = storage.get_availability(conn, train.number, day, seat_class.seat_class)
    if free is None:
        free = seat_class.total_seats
    return Availability(train.number, day, seat_class.seat_class,
                        seat_class.total_seats, free, seat_class.fare)


def check_availability(conn, train_number, travel_date, seat_class, today=None):
    """FR-02: free seats for one train / date / class."""
    day = _to_date(travel_date)
    train = _find_train(conn, train_number)
    _check_day(train, day, today)
    wanted = str(seat_class or "").strip().upper()
    classes = {c.seat_class.upper(): c for c in storage.get_seat_classes(conn, train.number)}
    if wanted not in classes:
        offered = ", ".join(c.seat_class for c in classes.values()) or "none"
        raise AvailabilityError(
            f"Class {wanted or '(blank)'} is not available on train "
            f"{train.number}. Choose from: {offered}")
    return _availability_for(conn, train, day, classes[wanted])


def list_availability(conn, train_number, travel_date, today=None):
    """FR-02: availability of every class on a train for one date."""
    day = _to_date(travel_date)
    train = _find_train(conn, train_number)
    _check_day(train, day, today)
    return [_availability_for(conn, train, day, sc)
            for sc in storage.get_seat_classes(conn, train.number)]
"""SQLite storage for the Railway Reservation System (TASK-01, NFR-05).

All SQL lives in this one file, so the rest of the project never touches SQL.
Every function takes the connection returned by connect() as its first argument.

Dates are stored as ISO text ('2026-11-02') and come back as datetime.date.
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from railway.models import CANCELLED, Booking, Passenger, SeatClass, Traveller, Train

# Always the project folder, no matter where the program is started from.
# Set the RAILWAY_DB environment variable to use a different file.
DEFAULT_DB_PATH = str(Path(__file__).resolve().parents[2] / "railway.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS trains (
    number      TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    source      TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure   TEXT NOT NULL,
    runs_on     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS seat_classes (
    train_number TEXT NOT NULL REFERENCES trains(number),
    seat_class   TEXT NOT NULL,
    total_seats  INTEGER NOT NULL CHECK (total_seats >= 0),
    fare         REAL NOT NULL CHECK (fare >= 0),
    PRIMARY KEY (train_number, seat_class)
);

CREATE TABLE IF NOT EXISTS availability (
    train_number TEXT NOT NULL,
    travel_date  TEXT NOT NULL,
    seat_class   TEXT NOT NULL,
    free_seats   INTEGER NOT NULL CHECK (free_seats >= 0),
    PRIMARY KEY (train_number, travel_date, seat_class),
    FOREIGN KEY (train_number, seat_class)
        REFERENCES seat_classes(train_number, seat_class)
);

CREATE TABLE IF NOT EXISTS passengers (
    email         TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'passenger'
                  CHECK (role IN ('passenger', 'admin'))
);

CREATE TABLE IF NOT EXISTS bookings (
    pnr             TEXT PRIMARY KEY,
    passenger_email TEXT NOT NULL REFERENCES passengers(email),
    train_number    TEXT NOT NULL,
    travel_date     TEXT NOT NULL,
    seat_class      TEXT NOT NULL,
    passengers      INTEGER NOT NULL CHECK (passengers BETWEEN 1 AND 6),
    fare            REAL NOT NULL CHECK (fare >= 0),
    status          TEXT NOT NULL CHECK (status IN ('CONFIRMED', 'CANCELLED')),
    FOREIGN KEY (train_number, seat_class)
        REFERENCES seat_classes(train_number, seat_class)
);

CREATE TABLE IF NOT EXISTS travellers (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    pnr    TEXT NOT NULL REFERENCES bookings(pnr),
    name   TEXT NOT NULL,
    age    INTEGER NOT NULL CHECK (age BETWEEN 1 AND 120),
    gender TEXT NOT NULL
);

-- One row per allocated seat. The UNIQUE rule means the database itself
-- refuses to give the same seat to two passengers (NFR-03).
CREATE TABLE IF NOT EXISTS seat_allocations (
    pnr          TEXT NOT NULL REFERENCES bookings(pnr),
    train_number TEXT NOT NULL,
    travel_date  TEXT NOT NULL,
    seat_class   TEXT NOT NULL,
    seat_number  INTEGER NOT NULL CHECK (seat_number >= 1),
    UNIQUE (train_number, travel_date, seat_class, seat_number)
);
"""


class StorageError(ValueError):
    """Raised when data cannot be saved (duplicate, unknown reference, bad value)."""


# ---------------------------------------------------------------- helpers

def _iso(value):
    return value.isoformat() if isinstance(value, date) else str(value)


def _encode_days(runs_on):
    return ",".join(str(d) for d in runs_on)


def _decode_days(text):
    return tuple(int(d) for d in text.split(",") if d != "")


@contextmanager
def _write(conn, what):
    """Run writes as one all-or-nothing step; turn DB errors into StorageError."""
    try:
        with conn:
            yield
    except sqlite3.IntegrityError as exc:
        raise StorageError(f"Could not save {what}: {exc}") from exc


# ------------------------------------------------------------- connection

def init_db(conn):
    """Create all tables if they do not exist yet."""
    conn.executescript(SCHEMA)


def connect(path=None):
    """Open (and set up) the database. Use ':memory:' for a throw-away test DB.

    With no path it uses $RAILWAY_DB if set, otherwise DEFAULT_DB_PATH.
    """
    conn = sqlite3.connect(path or os.environ.get("RAILWAY_DB") or DEFAULT_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    return conn


# ----------------------------------------------------------------- trains

def add_train(conn, train, seat_classes=()):
    """Save a train and its seat classes together (all or nothing)."""
    with _write(conn, f"train {train.number}"):
        conn.execute(
            "INSERT INTO trains VALUES (?, ?, ?, ?, ?, ?)",
            (train.number, train.name, train.source, train.destination,
             train.departure, _encode_days(train.runs_on)),
        )
        for sc in seat_classes:
            conn.execute(
                "INSERT INTO seat_classes VALUES (?, ?, ?, ?)",
                (sc.train_number, sc.seat_class, sc.total_seats, sc.fare),
            )


def _train_from_row(row):
    return Train(row["number"], row["name"], row["source"], row["destination"],
                 row["departure"], _decode_days(row["runs_on"]))


def get_train(conn, number):
    row = conn.execute("SELECT * FROM trains WHERE number = ?", (number,)).fetchone()
    return _train_from_row(row) if row else None


def list_trains(conn):
    rows = conn.execute("SELECT * FROM trains ORDER BY number").fetchall()
    return [_train_from_row(r) for r in rows]


def get_seat_classes(conn, train_number):
    rows = conn.execute(
        "SELECT * FROM seat_classes WHERE train_number = ? ORDER BY seat_class",
        (train_number,),
    ).fetchall()
    return [SeatClass(r["train_number"], r["seat_class"], r["total_seats"], r["fare"])
            for r in rows]


# ----------------------------------------------------------- availability

def set_availability(conn, train_number, travel_date, seat_class, free_seats):
    """Set the number of free seats for (train, date, class)."""
    with _write(conn, f"availability for train {train_number}"):
        conn.execute(
            "INSERT INTO availability VALUES (?, ?, ?, ?) "
            "ON CONFLICT(train_number, travel_date, seat_class) "
            "DO UPDATE SET free_seats = excluded.free_seats",
            (train_number, _iso(travel_date), seat_class, free_seats),
        )


def get_availability(conn, train_number, travel_date, seat_class):
    """Free seats, or None if nothing is recorded for that train/date/class."""
    row = conn.execute(
        "SELECT free_seats FROM availability "
        "WHERE train_number = ? AND travel_date = ? AND seat_class = ?",
        (train_number, _iso(travel_date), seat_class),
    ).fetchone()
    return row["free_seats"] if row else None


def load_availability(conn):
    """All availability as {(train_number, travel_date, seat_class): free_seats}.

    Same shape the dict-based code in cancellation.py already uses.
    """
    rows = conn.execute("SELECT * FROM availability").fetchall()
    return {(r["train_number"], date.fromisoformat(r["travel_date"]), r["seat_class"]):
            r["free_seats"] for r in rows}


def save_availability(conn, availability):
    """Write a {(train_number, travel_date, seat_class): free_seats} dict back."""
    for (train_number, travel_date, seat_class), free in availability.items():
        set_availability(conn, train_number, travel_date, seat_class, free)


# ------------------------------------------------------------- passengers

def add_passenger(conn, passenger):
    with _write(conn, f"passenger {passenger.email}"):
        conn.execute(
            "INSERT INTO passengers VALUES (?, ?, ?, ?)",
            (passenger.email, passenger.name, passenger.password_hash, passenger.role),
        )


def _passenger_from_row(row):
    return Passenger(row["email"], row["name"], row["password_hash"], row["role"])


def get_passenger(conn, email):
    row = conn.execute("SELECT * FROM passengers WHERE email = ?", (email,)).fetchone()
    return _passenger_from_row(row) if row else None


def load_passengers(conn):
    """All passengers as {email: Passenger} (same shape registration.py uses)."""
    rows = conn.execute("SELECT * FROM passengers").fetchall()
    return {r["email"]: _passenger_from_row(r) for r in rows}


# --------------------------------------------------------------- bookings

def add_booking(conn, booking, travellers=()):
    """Save a booking and its travellers together (all or nothing)."""
    with _write(conn, f"booking {booking.pnr}"):
        conn.execute(
            "INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (booking.pnr, booking.passenger_email, booking.train_number,
             _iso(booking.travel_date), booking.seat_class, booking.passengers,
             booking.fare, booking.status),
        )
        for t in travellers:
            conn.execute(
                "INSERT INTO travellers (pnr, name, age, gender) VALUES (?, ?, ?, ?)",
                (booking.pnr, t.name, t.age, t.gender),
            )


def _booking_from_row(row):
    return Booking(row["pnr"], row["passenger_email"], row["train_number"],
                   date.fromisoformat(row["travel_date"]), row["seat_class"],
                   row["passengers"], row["fare"], row["status"])


def get_booking(conn, pnr):
    row = conn.execute("SELECT * FROM bookings WHERE pnr = ?", (pnr,)).fetchone()
    return _booking_from_row(row) if row else None


def list_bookings(conn, passenger_email=None):
    """All bookings, or only one passenger's if an email is given."""
    if passenger_email is None:
        rows = conn.execute("SELECT * FROM bookings ORDER BY pnr").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM bookings WHERE passenger_email = ? ORDER BY pnr",
            (passenger_email,),
        ).fetchall()
    return [_booking_from_row(r) for r in rows]


def load_bookings(conn):
    """All bookings as {pnr: Booking} (same shape cancellation.py uses)."""
    return {b.pnr: b for b in list_bookings(conn)}


def get_travellers(conn, pnr):
    rows = conn.execute(
        "SELECT name, age, gender FROM travellers WHERE pnr = ? ORDER BY id", (pnr,)
    ).fetchall()
    return [Traveller(r["name"], r["age"], r["gender"]) for r in rows]


def update_booking_status(conn, pnr, status):
    with _write(conn, f"status of booking {pnr}"):
        cur = conn.execute("UPDATE bookings SET status = ? WHERE pnr = ?", (status, pnr))
        if cur.rowcount == 0:
            raise StorageError(f"No booking found for PNR {pnr}.")


# -------------------------------------------------------- seat allocation

def add_seat_allocation(conn, pnr, train_number, travel_date, seat_class, seat_number):
    """Give one seat to a booking. Refuses if that seat is already taken (NFR-03)."""
    with _write(conn, f"seat {seat_number} on train {train_number}"):
        conn.execute(
            "INSERT INTO seat_allocations VALUES (?, ?, ?, ?, ?)",
            (pnr, train_number, _iso(travel_date), seat_class, seat_number),
        )


def get_seat_numbers(conn, pnr):
    rows = conn.execute(
        "SELECT seat_number FROM seat_allocations WHERE pnr = ? ORDER BY seat_number",
        (pnr,),
    ).fetchall()
    return [r["seat_number"] for r in rows]


def delete_seat_allocations(conn, pnr):
    """Free all seats held by a booking (used when it is cancelled)."""
    with conn:
        conn.execute("DELETE FROM seat_allocations WHERE pnr = ?", (pnr,))


# ----------------------------------------------------------- cancellation

def apply_cancellation(conn, pnr):
    """Cancel a booking in ONE all-or-nothing step (NFR-04).

    Marks the booking CANCELLED, gives its seats back to the free-seat count
    and frees its seat numbers. If no availability row exists yet, every seat
    counts as free (same rule as availability.py); the count never goes above
    the class capacity. Returns the number of seats released.
    """
    with _write(conn, f"cancellation of booking {pnr}"):
        row = conn.execute("SELECT * FROM bookings WHERE pnr = ?", (pnr,)).fetchone()
        if row is None:
            raise StorageError(f"No booking found for PNR {pnr}.")
        if row["status"] == CANCELLED:
            raise StorageError(f"Booking {pnr} is already cancelled.")

        total = conn.execute(
            "SELECT total_seats FROM seat_classes WHERE train_number = ? AND seat_class = ?",
            (row["train_number"], row["seat_class"]),
        ).fetchone()["total_seats"]
        current = conn.execute(
            "SELECT free_seats FROM availability "
            "WHERE train_number = ? AND travel_date = ? AND seat_class = ?",
            (row["train_number"], row["travel_date"], row["seat_class"]),
        ).fetchone()
        free = total if current is None else current["free_seats"]

        conn.execute("UPDATE bookings SET status = ? WHERE pnr = ?", (CANCELLED, pnr))
        conn.execute(
            "INSERT INTO availability VALUES (?, ?, ?, ?) "
            "ON CONFLICT(train_number, travel_date, seat_class) "
            "DO UPDATE SET free_seats = excluded.free_seats",
            (row["train_number"], row["travel_date"], row["seat_class"],
             min(total, free + row["passengers"])),
        )
        conn.execute("DELETE FROM seat_allocations WHERE pnr = ?", (pnr,))
    return row["passengers"]

"""Command-line front end for the Railway Reservation System (TASK-06).

Ties the Sprint 1 features together: register/login (FR-09, FR-10), search
(FR-01, FR-03), seat availability (FR-02), booking (FR-04), viewing bookings
and cancellation with refund preview (FR-06, FR-07).

Run from the repo root:
    python -m railway --seed        (first time: adds sample trains + demo user)
    python -m railway               (afterwards)
"""
import argparse
import getpass
from datetime import date

from railway import storage
from railway.auth import current_passenger, login, logout
from railway.availability import list_availability
from railway.cancellation import (
    calculate_refund,
    cancel_booking,
    validate_cancellation,
    validate_deadline,
)
from railway.demo_data import DEMO_EMAIL, DEMO_PASSWORD, seed_demo_data
from railway.models import ROLE_ADMIN, Traveller
from railway.registration import register_passenger
from railway.search import search_trains, stations_of

MAX_PASSENGERS = 6  # BR-01 (the booking code enforces it too)

MENU = """
=========== Railway Reservation System ===========
 1. Register          6. Book ticket
 2. Login             7. My bookings
 3. Logout            8. View booking by PNR
 4. Search trains     9. Cancel booking
 5. Check seats       0. Exit"""


def _load_booking_function():
    """Find the booking function from FR-04, or None if it is not merged yet.

    ADAPT HERE: if the booking module/function has a different name or
    signature, change this import and the call in App.book().
    """
    try:
        from railway.booking import book_ticket
    except ImportError:
        return None
    return book_ticket


class App:
    """One CLI session. `ask`/`say` are injectable so tests can script it."""

    def __init__(self, conn, ask=input, say=print, ask_secret=None,
                 today=None, now=None, book_ticket=None):
        self.conn = conn
        self.ask = ask
        self.say = say
        self.ask_secret = ask_secret or ask
        self.today = today      # None = real today (tests pass a fixed date)
        self.now = now          # None = real clock
        self.book_ticket = book_ticket
        self.sessions = {}
        self.token = None
        self.handlers = {
            "1": self.register, "2": self.login, "3": self.logout,
            "4": self.search, "5": self.check_seats, "6": self.book,
            "7": self.my_bookings, "8": self.view_booking, "9": self.cancel,
        }

    # ------------------------------------------------------------ main loop

    def run(self):
        while True:
            self.say(MENU)
            self.say(self._status())
            choice = self.ask("Choose an option: ").strip()
            if choice == "0":
                self.say("Goodbye.")
                return
            handler = self.handlers.get(choice)
            if handler is None:
                self.say("Invalid choice. Enter a number from the menu.")
                continue
            try:
                handler()
            except ValueError as err:   # all our domain errors are ValueErrors
                self.say(f"Error: {err}")

    def _status(self):
        if self.token in self.sessions:
            email = self.sessions[self.token]
            passenger = storage.get_passenger(self.conn, email)
            return f"Logged in as {passenger.name if passenger else email}"
        return "Not logged in"

    # -------------------------------------------------------------- helpers

    def _require_login(self):
        return current_passenger(
            self.token, storage.load_passengers(self.conn), self.sessions)

    def _ask_date(self, prompt):
        text = self.ask(prompt).strip()
        if not text:
            raise ValueError("Travel date is required.")
        try:
            return date.fromisoformat(text)
        except ValueError:
            raise ValueError("Travel date must be in YYYY-MM-DD format.") from None

    def _ask_int(self, prompt, label):
        try:
            return int(self.ask(prompt).strip())
        except ValueError:
            raise ValueError(f"{label} must be a whole number.") from None

    def _own_booking(self, pnr, passenger):
        """A passenger may only see their own bookings (admins see all)."""
        booking = storage.get_booking(self.conn, pnr) if pnr else None
        if booking is None or (booking.passenger_email != passenger.email
                               and passenger.role != ROLE_ADMIN):
            raise ValueError(f"No booking found for PNR {pnr or '(blank)'}.")
        return booking

    # ------------------------------------------------------------- accounts

    def register(self):
        name = self.ask("Full name: ")
        email = self.ask("Email: ")
        password = self.ask_secret("Password: ")
        passengers = storage.load_passengers(self.conn)
        passenger = register_passenger(name, email, password, passengers)
        storage.add_passenger(self.conn, passenger)
        self.say(f"Registered {passenger.name}. You can log in now.")

    def login(self):
        email = self.ask("Email: ")
        password = self.ask_secret("Password: ")
        passengers = storage.load_passengers(self.conn)
        self.token = login(email, password, passengers, self.sessions)
        self.say(f"{self._status()}.")

    def logout(self):
        logout(self.token, self.sessions)
        self.token = None
        self.say("Logged out.")

    # ----------------------------------------------------- search and seats

    def search(self):
        source = self.ask("From: ")
        destination = self.ask("To: ")
        day = self._ask_date("Travel date (YYYY-MM-DD): ")
        trains = storage.list_trains(self.conn)
        found = search_trains(source, destination, day, trains,
                              stations_of(trains), today=self.today)
        if not found:
            self.say("No trains found for that route and date.")
            return
        self.say(f"\n{len(found)} train(s) found on {day.isoformat()}:")
        for train in found:
            self.say(f"\n{train.number}  {train.name}   "
                     f"{train.source} -> {train.destination}   dep {train.departure}")
            self._print_classes(train.number, day)

    def check_seats(self):
        number = self.ask("Train number: ")
        day = self._ask_date("Travel date (YYYY-MM-DD): ")
        self._print_classes(number.strip(), day)

    def _print_classes(self, train_number, day):
        for info in list_availability(self.conn, train_number, day, today=self.today):
            seats = (f"{info.free_seats} seats free" if info.free_seats
                     else "SOLD OUT")
            self.say(f"    {info.seat_class:<4} Rs {info.fare:<8.2f} {seats}")

    # --------------------------------------------------------------- booking

    def book(self):
        passenger = self._require_login()
        book_ticket = self.book_ticket or _load_booking_function()
        if book_ticket is None:
            self.say("Booking is not available yet (FR-04 has not been merged).")
            return
        train_number = self.ask("Train number: ").strip()
        day = self._ask_date("Travel date (YYYY-MM-DD): ")
        seat_class = self.ask("Class (for example 3AC, SL): ").strip().upper()
        count = self._ask_int("Number of passengers: ", "Number of passengers")
        if not 1 <= count <= MAX_PASSENGERS:
            raise ValueError(f"Passengers must be between 1 and {MAX_PASSENGERS}.")
        travellers = []
        for i in range(1, count + 1):
            name = self.ask(f"Passenger {i} name: ").strip()
            age = self._ask_int(f"Passenger {i} age: ", "Age")
            gender = self.ask(f"Passenger {i} gender (M/F/O): ").strip()
            travellers.append(Traveller(name, age, gender))
        # ADAPT HERE if Urav's function takes different arguments.
        result = book_ticket(self.conn, passenger.email, train_number, day,
                             seat_class, travellers)
        self.say(f"Booking confirmed. PNR: {getattr(result, 'pnr', result)}")

    def my_bookings(self):
        passenger = self._require_login()
        bookings = storage.list_bookings(self.conn, passenger.email)
        if not bookings:
            self.say("You have no bookings yet.")
            return
        for b in bookings:
            self.say(f"{b.pnr}  train {b.train_number}  {b.travel_date.isoformat()}  "
                     f"{b.seat_class}  x{b.passengers}  Rs {b.fare:.2f}  {b.status}")

    def view_booking(self):
        passenger = self._require_login()
        pnr = self.ask("PNR: ").strip()
        b = self._own_booking(pnr, passenger)
        self.say(f"PNR {b.pnr}   Status: {b.status}")
        self.say(f"Train {b.train_number}  on {b.travel_date.isoformat()}  "
                 f"class {b.seat_class}  fare Rs {b.fare:.2f}")
        for t in storage.get_travellers(self.conn, b.pnr):
            self.say(f"  - {t.name}, {t.age}, {t.gender}")
        seats = storage.get_seat_numbers(self.conn, b.pnr)
        if seats:
            self.say("Seats: " + ", ".join(str(s) for s in seats))

    # ---------------------------------------------------------- cancellation

    def cancel(self):
        passenger = self._require_login()
        pnr = self.ask("PNR to cancel: ").strip()
        booking = self._own_booking(pnr, passenger)
        validate_cancellation(pnr, {pnr: booking})
        train = storage.get_train(self.conn, booking.train_number)
        validate_deadline(booking.travel_date, train.departure, self.now)
        refund = calculate_refund(booking.fare, booking.travel_date,
                                  train.departure, self.now)
        self.say(f"Refund if you cancel now: Rs {refund:.2f}")
        if self.ask("Cancel this booking? (y/n): ").strip().lower() != "y":
            self.say("Booking not cancelled.")
            return
        result = cancel_booking(self.conn, pnr, self.now)
        self.say(f"Booking {result.pnr} cancelled. "
                 f"{result.seats_released} seat(s) released. "
                 f"Refund: Rs {result.refund_amount:.2f}")


def main(argv=None, ask=input, say=print, ask_secret=getpass.getpass):
    parser = argparse.ArgumentParser(prog="railway", description=__doc__.splitlines()[0])
    parser.add_argument("--db", default=storage.DEFAULT_DB_PATH,
                        help="database file (default: %(default)s)")
    parser.add_argument("--seed", action="store_true",
                        help="add sample trains and a demo account first")
    args = parser.parse_args(argv)

    conn = storage.connect(args.db)
    try:
        if args.seed and seed_demo_data(conn):
            say(f"Sample data added. Demo login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        App(conn, ask=ask, say=say, ask_secret=ask_secret).run()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
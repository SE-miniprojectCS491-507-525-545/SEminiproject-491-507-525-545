
"""Command-line front end for the Railway Reservation System (TASK-06).

Ties the Sprint 1 features together: registration/login, train search,
seat availability, booking, booking management, cancellation and refunds.
Also supports FR-13: admin train creation.
"""

import argparse
import getpass
import math
import re
from datetime import date, datetime

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
from railway.models import ROLE_ADMIN, SeatClass, Train, Traveller
from railway.traveller_validation import TravellerError, validate_traveller
from railway.registration import register_passenger
from railway.search import SearchError, search_trains, stations_of
from railway.search_help import (
    DATE_PROMPT,
    friendly_date,
    no_results_hint,
    unknown_station_hint,
)


MAX_PASSENGERS = 6  # BR-01

MENU = """
=========== Railway Reservation System ===========
 1. Register          6. Book ticket
 2. Login             7. My bookings
 3. Logout            8. View booking by PNR
 4. Search trains     9. Cancel booking
 5. Check seats      10. Admin: Add train
11. Admin: Update train
12. Admin: Remove train
 0. Exit
"""


def _load_booking_function():
    """Find the booking function from FR-04, or None if unavailable."""
    try:
        from railway.booking import book_ticket
    except ImportError:
        return None
    return book_ticket


class App:
    """One CLI session. ask/say are injectable so tests can script it."""

    def __init__(
        self,
        conn,
        ask=input,
        say=print,
        ask_secret=None,
        today=None,
        now=None,
        book_ticket=None,
    ):
        self.conn = conn
        self.ask = ask
        self.say = say
        self.ask_secret = ask_secret or ask
        self.today = today
        self.now = now
        self.book_ticket = book_ticket
        self.sessions = {}
        self.token = None

        self.handlers = {
            "1": self.register,
            "2": self.login,
            "3": self.logout,
            "4": self.search,
            "5": self.check_seats,
            "6": self.book,
            "7": self.my_bookings,
            "8": self.view_booking,
            "9": self.cancel,
            "10": self.add_train,
            "11": self.update_train,
            "12": self.remove_train,
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
            except ValueError as err:
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
            self.token,
            storage.load_passengers(self.conn),
            self.sessions,
        )

    def _require_admin(self):
        """Require an authenticated administrator."""
        passenger = self._require_login()

        if passenger.role != ROLE_ADMIN:
            raise ValueError("Admin access required.")

        return passenger

    def _ask_date(self, prompt):
        return friendly_date(self.ask(prompt), self.today)

    def _ask_int(self, prompt, label):
        try:
            return int(self.ask(prompt).strip())
        except ValueError:
            raise ValueError(
                f"{label} must be a whole number."
            ) from None

    def _own_booking(self, pnr, passenger):
        """Passengers see their own bookings; admins can see all."""
        booking = storage.get_booking(self.conn, pnr) if pnr else None

        if (
            booking is None
            or (
                booking.passenger_email != passenger.email
                and passenger.role != ROLE_ADMIN
            )
        ):
            raise ValueError(
                f"No booking found for PNR {pnr or '(blank)'}.",
            )

        return booking

    # ------------------------------------------------------------- accounts

    def register(self):
        name = self.ask("Full name: ")
        email = self.ask("Email: ")
        password = self.ask_secret("Password: ")

        passengers = storage.load_passengers(self.conn)
        passenger = register_passenger(
            name,
            email,
            password,
            passengers,
        )
        storage.add_passenger(self.conn, passenger)

        self.say(
            f"Registered {passenger.name}. You can log in now."
        )

    def login(self):
        email = self.ask("Email: ")
        password = self.ask_secret("Password: ")

        passengers = storage.load_passengers(self.conn)
        self.token = login(
            email,
            password,
            passengers,
            self.sessions,
        )

        self.say(f"{self._status()}.")

    def logout(self):
        logout(self.token, self.sessions)
        self.token = None
        self.say("Logged out.")

    # ----------------------------------------------------- search and seats

    def search(self):
        trains = storage.list_trains(self.conn)
        stations = stations_of(trains)

        if stations:
            self.say("Stations: " + ", ".join(stations))
            self.say("(Station names are not case-sensitive.)")

        source = self.ask("From: ")
        destination = self.ask("To: ")
        day = self._ask_date(DATE_PROMPT)

        try:
            found = search_trains(
                source,
                destination,
                day,
                trains,
                stations,
                today=self.today,
            )
        except SearchError as err:
            message = str(err)

            if message.startswith("Unknown station"):
                known = {name.lower() for name in stations}
                unknown = next(
                    (
                        typed for typed in (source, destination)
                        if typed.strip().lower() not in known
                    ),
                    source,
                )
                message += " " + unknown_station_hint(unknown, stations)

            raise ValueError(message) from None

        if not found:
            self.say("No trains found for that route and date.")
            self.say(no_results_hint(trains, source, destination))
            return

        self.say(
            f"\n{len(found)} train(s) found on {day.isoformat()}:"
        )

        for train in found:
            self.say(
                f"\n{train.number}  {train.name}   "
                f"{train.source} -> {train.destination}   "
                f"dep {train.departure}"
            )
            self._print_classes(train.number, day)

        self.say("\nTo book, choose option 6 and enter the train number above.")

    def check_seats(self):
        number = self.ask("Train number: ").strip()
        day = self._ask_date(DATE_PROMPT)
        self._print_classes(number, day)

    def _print_classes(self, train_number, day):
        for info in list_availability(
            self.conn,
            train_number,
            day,
            today=self.today,
        ):
            seats = (
                f"{info.free_seats} seats free"
                if info.free_seats
                else "SOLD OUT"
            )
            self.say(
                f"    {info.seat_class:<4} "
                f"Rs {info.fare:<8.2f} {seats}"
            )

    # ---------------------------------------------------------- FR-13 admin

    def update_train(self):
        try:
            self._require_admin()
            number = self.ask("Train number to update: ").strip()
            train = storage.get_train(self.conn, number)

            if train is None:
                self.say("Train not found.")
                return

            self.say("Press Enter to keep the current value.")
            name = self.ask(f"Train name [{train.name}]: ").strip() or train.name
            source = self.ask(f"Source [{train.source}]: ").strip() or train.source
            destination = self.ask(
                f"Destination [{train.destination}]: "
            ).strip() or train.destination
            departure = self.ask(
                f"Departure time [{train.departure}]: "
            ).strip() or train.departure

            current_days = ",".join(str(d) for d in train.runs_on)
            days_input = self.ask(
                f"Running days (0=Mon ... 6=Sun) [{current_days}]: "
            ).strip()

            days = (
                tuple(sorted(set(int(d.strip()) for d in days_input.split(","))))
                if days_input else train.runs_on
            )

            if not name or not source or not destination:
                self.say("Name, source and destination cannot be empty.")
                return
            if source.lower() == destination.lower():
                self.say("Source and destination must be different.")
                return
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", departure):
                self.say("Invalid departure time. Use HH:MM.")
                return
            if not days or any(day < 0 or day > 6 for day in days):
                self.say("Invalid running days. Enter values from 0 to 6.")
                return

            updated = Train(
                train.number, name, source, destination, departure, days
            )
            storage.update_train(self.conn, updated)
            self.say(f"Train {number} updated successfully.")

        except (ValueError, TypeError) as exc:
            self.say(f"Could not update train: {exc}")

    def remove_train(self):
        try:
            self._require_admin()
            number = self.ask("Train number to remove: ").strip()
            train = storage.get_train(self.conn, number)

            if train is None:
                self.say("Train not found.")
                return

            confirm = self.ask(
                f"Remove {train.name} ({number})? Type Y to confirm: "
            ).strip().upper()

            if confirm != "Y":
                self.say("Removal cancelled.")
                return

            storage.remove_train(self.conn, number)
            self.say(f"Train {number} removed successfully.")

        except ValueError as exc:
            self.say(f"Could not remove train: {exc}")

    def add_train(self):
        """Add a train and its initial seat class. Admin only."""
        self._require_admin()

        number = self.ask("Train number: ").strip()
        name = self.ask("Train name: ").strip()
        source = self.ask("Source station: ").strip()
        destination = self.ask("Destination station: ").strip()
        departure = self.ask("Departure time (HH:MM): ").strip()

        # Required-field validation.
        required_fields = {
            "Train number": number,
            "Train name": name,
            "Source station": source,
            "Destination station": destination,
            "Departure time": departure,
        }

        for label, value in required_fields.items():
            if not value:
                raise ValueError(f"{label} is required.")

        if source.casefold() == destination.casefold():
            raise ValueError(
                "Source and destination must be different."
            )

        # Validate the time and require exactly HH:MM.
        if not re.fullmatch(r"\d{2}:\d{2}", departure):
            raise ValueError(
                "Departure time must be in HH:MM format."
            )

        try:
            datetime.strptime(departure, "%H:%M")
        except ValueError:
            raise ValueError(
                "Departure time must be a valid time in HH:MM format."
            ) from None

        # Parse operating days: Monday=0 through Sunday=6.
        days_text = self.ask(
            "Operating days (0=Mon to 6=Sun, comma-separated): "
        ).strip()

        if not days_text:
            raise ValueError("At least one operating day is required.")

        try:
            runs_on = tuple(
                sorted(
                    {
                        int(day.strip())
                        for day in days_text.split(",")
                    }
                )
            )
        except ValueError:
            raise ValueError(
                "Operating days must be numbers from 0 to 6."
            ) from None

        if not runs_on or any(day < 0 or day > 6 for day in runs_on):
            raise ValueError(
                "Operating days must be numbers from 0 to 6."
            )

        # Validate the initial seat class.
        seat_class_name = self.ask(
            "Seat class (for example SL or 3AC): "
        ).strip().upper()

        if not seat_class_name:
            raise ValueError("Seat class is required.")

        total_seats = self._ask_int(
            "Total seats: ",
            "Total seats",
        )

        if total_seats <= 0:
            raise ValueError("Total seats must be greater than zero.")

        fare_text = self.ask("Fare (Rs): ").strip()

        if not fare_text:
            raise ValueError("Fare is required.")

        try:
            fare = float(fare_text)
        except ValueError:
            raise ValueError("Fare must be a valid number.") from None

        if not math.isfinite(fare) or fare < 0:
            raise ValueError(
                "Fare must be a finite, non-negative number."
            )

        # Friendly duplicate-number validation.
        if storage.get_train(self.conn, number) is not None:
            raise ValueError(
                f"Train number {number} already exists."
            )

        train = Train(
            number=number,
            name=name,
            source=source,
            destination=destination,
            departure=departure,
            runs_on=runs_on,
        )

        seat_class = SeatClass(
            train_number=number,
            seat_class=seat_class_name,
            total_seats=total_seats,
            fare=fare,
        )

        # The storage layer saves the train and seat class together.
        storage.add_train(self.conn, train, [seat_class])

        self.say(f"Train {number} added successfully.")

    # --------------------------------------------------------------- booking

    def book(self):
        passenger = self._require_login()
        book_ticket = self.book_ticket or _load_booking_function()

        if book_ticket is None:
            self.say(
                "Booking is not available yet "
                "(FR-04 has not been merged)."
            )
            return

        train_number = self.ask("Train number: ").strip()
        day = self._ask_date(DATE_PROMPT)
        seat_class = self.ask(
            "Class (for example 3AC, SL): "
        ).strip().upper()
        count = self._ask_int(
            "Number of passengers: ",
            "Number of passengers",
        )

        if not 1 <= count <= MAX_PASSENGERS:
            raise ValueError(
                f"Passengers must be between 1 and {MAX_PASSENGERS}."
            )

        travellers = []

        for i in range(1, count + 1):
            name = self.ask(f"Passenger {i} name: ").strip()
            age = self._ask_int(
                f"Passenger {i} age: ",
                "Age",
            )
            gender = self.ask(
                f"Passenger {i} gender (M/F/O): "
            ).strip()

            # Check each passenger straight away so the error names them
            # (FR-05) instead of failing after every detail was typed in.
            try:
                travellers.append(validate_traveller(Traveller(name, age, gender), i))
            except TravellerError as exc:
                raise ValueError(str(exc)) from None

        result = book_ticket(
            self.conn,
            passenger.email,
            train_number,
            day,
            seat_class,
            travellers,
        )

        self.say(
            f"Booking confirmed. PNR: "
            f"{getattr(result, 'pnr', result)}"
        )

    def my_bookings(self):
        passenger = self._require_login()
        bookings = storage.list_bookings(
            self.conn,
            passenger.email,
        )

        if not bookings:
            self.say("You have no bookings yet.")
            return

        for booking in bookings:
            self.say(
                f"{booking.pnr}  train {booking.train_number}  "
                f"{booking.travel_date.isoformat()}  "
                f"{booking.seat_class}  x{booking.passengers}  "
                f"Rs {booking.fare:.2f}  {booking.status}"
            )

    def view_booking(self):
        passenger = self._require_login()
        pnr = self.ask("PNR: ").strip()
        booking = self._own_booking(pnr, passenger)

        self.say(f"PNR {booking.pnr}   Status: {booking.status}")
        self.say(
            f"Train {booking.train_number}  "
            f"on {booking.travel_date.isoformat()}  "
            f"class {booking.seat_class}  "
            f"fare Rs {booking.fare:.2f}"
        )

        for traveller in storage.get_travellers(
            self.conn,
            booking.pnr,
        ):
            self.say(
                f"  - {traveller.name}, "
                f"{traveller.age}, {traveller.gender}"
            )

        seats = storage.get_seat_numbers(
            self.conn,
            booking.pnr,
        )

        if seats:
            self.say(
                "Seats: " + ", ".join(str(seat) for seat in seats)
            )

    # ---------------------------------------------------------- cancellation

    def cancel(self):
        passenger = self._require_login()
        pnr = self.ask("PNR to cancel: ").strip()
        booking = self._own_booking(pnr, passenger)

        validate_cancellation(pnr, {pnr: booking})

        train = storage.get_train(
            self.conn,
            booking.train_number,
        )

        validate_deadline(
            booking.travel_date,
            train.departure,
            self.now,
        )

        refund = calculate_refund(
            booking.fare,
            booking.travel_date,
            train.departure,
            self.now,
        )

        self.say(f"Refund if you cancel now: Rs {refund:.2f}")

        if self.ask(
            "Cancel this booking? (y/n): "
        ).strip().lower() != "y":
            self.say("Booking not cancelled.")
            return

        result = cancel_booking(self.conn, pnr, self.now)

        self.say(
            f"Booking {result.pnr} cancelled. "
            f"{result.seats_released} seat(s) released. "
            f"Refund: Rs {result.refund_amount:.2f}"
        )


def main(
    argv=None,
    ask=input,
    say=print,
    ask_secret=getpass.getpass,
):
    parser = argparse.ArgumentParser(
        prog="railway",
        description=__doc__.splitlines()[0],
    )
    parser.add_argument(
        "--db",
        default=storage.DEFAULT_DB_PATH,
        help="database file (default: %(default)s)",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="add sample trains and a demo account first",
    )
    args = parser.parse_args(argv)

    conn = storage.connect(args.db)

    try:
        if args.seed and seed_demo_data(conn):
            say(
                f"Sample data added. Demo login: "
                f"{DEMO_EMAIL} / {DEMO_PASSWORD}"
            )

        App(
            conn,
            ask=ask,
            say=say,
            ask_secret=ask_secret,
        ).run()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
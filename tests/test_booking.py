import threading
from datetime import date, datetime

import pytest

from railway import storage
from railway.booking import BookingError, Ticket, book_ticket, format_ticket
from railway.cancellation import cancel_booking
from railway.models import Passenger, SeatClass, Traveller, Train

TRAVEL = date(2026, 11, 2)            # a Monday; the train runs Mon, Wed, Fri
TODAY = date(2026, 10, 21)
EARLY = datetime(2026, 10, 21, 10, 0)


def people(n=1):
    return [Traveller(f"Person {i}", 20 + i, "F") for i in range(1, n + 1)]


def seed(conn):
    storage.add_train(conn, Train("12627", "Karnataka Express", "Bengaluru", "Delhi",
                                  "19:20", (0, 2, 4)),
                      [SeatClass("12627", "3AC", 60, 1500.0),
                       SeatClass("12627", "1AC", 2, 3000.0)])
    storage.add_passenger(conn, Passenger("a@x.com", "Asha", "salt$hash"))
    storage.add_passenger(conn, Passenger("b@x.com", "Bina", "salt$hash"))


@pytest.fixture
def conn():
    c = storage.connect(":memory:")
    seed(c)
    yield c
    c.close()


def book(conn, who="a@x.com", seat_class="3AC", n=1, day=TRAVEL, train="12627"):
    return book_ticket(conn, who, train, day, seat_class, people(n), today=TODAY)


# --- FR-04a: booking works (TC-BOOK-001, TC-BOOK-002) ---

def test_valid_booking_returns_a_confirmed_ticket(conn):
    ticket = book(conn, n=2)
    assert isinstance(ticket, Ticket)
    assert ticket.status == "CONFIRMED"
    assert (ticket.train_number, ticket.train_name) == ("12627", "Karnataka Express")
    assert (ticket.travel_date, ticket.seat_class) == (TRAVEL, "3AC")
    assert ticket.fare == 3000.0
    assert len(ticket.pnr) == 10 and ticket.pnr.isdigit()


def test_booking_lowers_the_free_seat_count_by_the_number_booked(conn):
    book(conn, n=2)
    assert storage.get_availability(conn, "12627", TRAVEL, "3AC") == 58


def test_booking_is_saved_with_its_travellers_and_seats(conn):
    ticket = book(conn, n=2)
    saved = storage.get_booking(conn, ticket.pnr)
    assert (saved.passenger_email, saved.passengers, saved.fare) == ("a@x.com", 2, 3000.0)
    assert [t.name for t in storage.get_travellers(conn, ticket.pnr)] == ["Person 1", "Person 2"]
    assert storage.get_seat_numbers(conn, ticket.pnr) == [1, 2]


def test_each_booking_gets_its_own_pnr_and_the_next_seats(conn):
    first, second = book(conn, n=2), book(conn, who="b@x.com", n=2)
    assert first.pnr != second.pnr
    assert (first.seat_numbers, second.seat_numbers) == ((1, 2), (3, 4))


def test_class_name_is_saved_in_its_proper_form(conn):
    assert book(conn, seat_class="3ac").seat_class == "3AC"
    assert storage.get_availability(conn, "12627", TRAVEL, "3AC") == 59


def test_email_is_matched_ignoring_case_and_spaces(conn):
    assert book(conn, who="  A@X.com ").pnr


def test_other_dates_and_classes_are_not_affected(conn):
    book(conn, n=2)
    assert storage.get_availability(conn, "12627", date(2026, 11, 4), "3AC") is None
    assert storage.get_availability(conn, "12627", TRAVEL, "1AC") is None


# --- login needed ---

@pytest.mark.parametrize("who", ["", "   ", None, "ghost@x.com"])
def test_booking_needs_a_registered_account(conn, who):
    with pytest.raises(BookingError, match="log in"):
        book(conn, who=who)
    assert storage.list_bookings(conn) == []


# --- FR-05 / BR-01 reach the booking (TC-BOOK-003/004/005) ---

@pytest.mark.parametrize("bad,message", [
    (Traveller("", 30, "F"), "name is required"),
    (Traveller("Asha", 0, "F"), "age"),
    (Traveller("Asha", 121, "F"), "age"),
    (Traveller("Asha", 30, "?"), "gender"),
])
def test_invalid_traveller_details_stop_the_booking(conn, bad, message):
    with pytest.raises(BookingError, match=message):
        book_ticket(conn, "a@x.com", "12627", TRAVEL, "3AC", [bad], today=TODAY)
    assert storage.list_bookings(conn) == []
    assert storage.get_availability(conn, "12627", TRAVEL, "3AC") is None


def test_seven_passengers_are_refused(conn):
    with pytest.raises(BookingError, match="at most 6"):
        book(conn, n=7)
    assert storage.list_bookings(conn) == []


def test_six_passengers_are_accepted(conn):
    assert len(book(conn, n=6).seat_numbers) == 6


# --- train / date / class checks ---

@pytest.mark.parametrize("kwargs,message", [
    (dict(train="99999"), "not found"),
    (dict(day=date(2026, 10, 1)), "past"),
    (dict(day=date(2026, 11, 3)), "does not run"),
    (dict(seat_class="2AC"), "not available on train"),
])
def test_bad_train_date_or_class_is_refused(conn, kwargs, message):
    with pytest.raises(BookingError, match=message):
        book(conn, **kwargs)
    assert storage.list_bookings(conn) == []


# --- not enough seats (NFR-03 wording) ---

def test_booking_more_seats_than_are_left_is_refused_and_changes_nothing(conn):
    book(conn, seat_class="1AC", n=1)
    with pytest.raises(BookingError, match=r"Only 1 seat\(s\) left in 1AC; you asked for 2"):
        book(conn, who="b@x.com", seat_class="1AC", n=2)
    assert storage.get_availability(conn, "12627", TRAVEL, "1AC") == 1
    assert len(storage.list_bookings(conn)) == 1


def test_a_full_class_says_no_seats_available(conn):
    book(conn, seat_class="1AC", n=2)
    with pytest.raises(BookingError, match="No seats available in 1AC"):
        book(conn, who="b@x.com", seat_class="1AC")
    assert storage.get_availability(conn, "12627", TRAVEL, "1AC") == 0


# --- all or nothing ---

def test_a_failure_part_way_leaves_nothing_changed(conn):
    conn.execute("CREATE TRIGGER block_seats BEFORE INSERT ON seat_allocations "
                 "BEGIN SELECT RAISE(ABORT, 'simulated failure'); END")
    with pytest.raises(BookingError):
        book(conn, n=2)
    assert storage.list_bookings(conn) == []
    assert storage.get_availability(conn, "12627", TRAVEL, "3AC") is None
    assert conn.execute("SELECT COUNT(*) FROM travellers").fetchone()[0] == 0


def test_booking_is_refused_if_availability_changed_after_the_check(conn, monkeypatch):
    """Someone else takes the seats between the check and the booking."""
    real = storage.book_seats

    def late(conn_, *args):
        storage.set_availability(conn_, "12627", TRAVEL, "3AC", 0)
        return real(conn_, *args)

    monkeypatch.setattr(storage, "book_seats", late)
    with pytest.raises(BookingError, match="No seats available"):
        book(conn)
    assert storage.list_bookings(conn) == []


# --- works with cancellation (NFR-04) ---

def test_cancelling_frees_the_seats_for_the_next_booking(conn):
    first = book(conn, seat_class="1AC", n=2)
    cancel_booking(conn, first.pnr, now=EARLY)
    assert storage.get_availability(conn, "12627", TRAVEL, "1AC") == 2
    second = book(conn, who="b@x.com", seat_class="1AC", n=2)
    assert second.seat_numbers == (1, 2)


# --- two people, one last seat (NFR-03, TC-BOOK-006) ---

def test_two_people_booking_the_last_seat_get_exactly_one_booking(tmp_path):
    path = str(tmp_path / "race.db")
    setup = storage.connect(path)
    seed(setup)
    book(setup, seat_class="1AC", n=1)            # one of the two 1AC seats left
    setup.close()

    outcomes, barrier = [], threading.Barrier(2)

    def attempt(email):
        own = storage.connect(path)
        barrier.wait()
        try:
            outcomes.append(("ok", book(own, who=email, seat_class="1AC").pnr))
        except BookingError as exc:
            outcomes.append(("refused", str(exc)))
        finally:
            own.close()

    threads = [threading.Thread(target=attempt, args=(e,)) for e in ("a@x.com", "b@x.com")]
    [t.start() for t in threads]
    [t.join() for t in threads]

    assert sorted(kind for kind, _ in outcomes) == ["ok", "refused"]
    assert any("No seats available" in text for kind, text in outcomes if kind == "refused")
    check = storage.connect(path)
    assert storage.get_availability(check, "12627", TRAVEL, "1AC") == 0
    assert sorted(storage.get_seat_numbers(check, b.pnr)[0] for b in storage.list_bookings(check)) == [1, 2]
    check.close()


# --- confirmation text ---

def test_confirmation_shows_pnr_train_date_class_and_fare(conn):
    ticket = book(conn, n=2)
    text = format_ticket(ticket)
    for expected in (ticket.pnr, "Karnataka Express", "2026-11-02", "3AC", "3000.00",
                     "Person 1", "seat 1", "seat 2"):
        assert expected in text

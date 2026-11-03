"""NFR-04: after a cancellation the seat count is right and visible straight away.

Covers the consistency checker, the next-request visibility rule, and several
people cancelling and booking at the same moment (each with its own connection).
"""
import random
import threading
import time
from datetime import date, datetime, timedelta

import pytest

from railway import availability, storage
from railway.booking import BookingError, book_ticket
from railway.cancellation import CancellationError, cancel_booking
from railway.consistency import find_inconsistencies, is_consistent
from railway.models import Passenger, SeatClass, Traveller, Train

DAY = date(2026, 11, 9)
TODAY = date(2026, 10, 26)
EARLY = datetime(2026, 10, 26, 10, 0)


def make_db(path, total_seats=4, people=8):
    conn = storage.connect(path)
    storage.add_train(conn, Train("T1", "Test Express", "A", "B", "10:00", tuple(range(7))),
                      [SeatClass("T1", "CC", total_seats, 100.0)])
    for i in range(people):
        storage.add_passenger(conn, Passenger(f"p{i}@x.com", f"P{i}", "salt$hash"))
    conn.close()


def travellers(n):
    return [Traveller(f"Person {i}", 30, "F") for i in range(1, n + 1)]


def book(conn, who=0, seats=1, day=DAY, train="T1", seat_class="CC"):
    return book_ticket(conn, f"p{who}@x.com", train, day, seat_class, travellers(seats),
                       today=TODAY)


def free(conn, day=DAY):
    return storage.get_availability(conn, "T1", day, "CC")


def run_together(path, jobs):
    """Run each job(conn) in its own thread and connection, all starting together."""
    results, problems = [None] * len(jobs), []
    barrier = threading.Barrier(len(jobs))

    def worker(index, job):
        conn = storage.connect(path)
        try:
            barrier.wait()
            try:
                results[index] = ("ok", job(conn))
            except (BookingError, CancellationError) as exc:
                results[index] = ("refused", str(exc))
        except Exception as exc:                       # anything else is a real bug
            problems.append(f"job {index}: {type(exc).__name__}: {exc}")
        finally:
            conn.close()

    threads = [threading.Thread(target=worker, args=(i, j)) for i, j in enumerate(jobs)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert not problems, problems
    return results


@pytest.fixture
def conn():
    c = storage.connect(":memory:")
    storage.add_train(c, Train("T1", "Test Express", "A", "B", "10:00", tuple(range(7))),
                      [SeatClass("T1", "CC", 4, 100.0)])
    for i in range(8):
        storage.add_passenger(c, Passenger(f"p{i}@x.com", f"P{i}", "salt$hash"))
    yield c
    c.close()


# ---------------------------------------------------------------- the checker

def test_an_empty_database_is_consistent(conn):
    assert find_inconsistencies(conn) == [] and is_consistent(conn)


def test_bookings_and_cancellations_keep_everything_consistent(conn):
    first, second = book(conn, 0, 2), book(conn, 1, 1)
    assert is_consistent(conn)
    cancel_booking(conn, first.pnr, now=EARLY)
    assert is_consistent(conn) and free(conn) == 3
    cancel_booking(conn, second.pnr, now=EARLY)
    assert is_consistent(conn) and free(conn) == 4


def test_checker_reports_a_wrong_free_count(conn):
    book(conn, 0, 2)
    conn.execute("UPDATE availability SET free_seats = free_seats + 1")
    problems = find_inconsistencies(conn)
    assert len(problems) == 1 and "shows 3 free seat(s)" in problems[0] and "2 should be free" in problems[0]


def test_checker_reports_a_booking_with_no_availability_row(conn):
    book(conn, 0, 2)
    conn.execute("DELETE FROM availability")
    assert any("shows 4 free seat(s)" in p for p in find_inconsistencies(conn))


def test_checker_reports_a_booking_that_lost_its_seat_numbers(conn):
    ticket = book(conn, 0, 2)
    conn.execute("DELETE FROM seat_allocations WHERE pnr = ?", (ticket.pnr,))
    problems = find_inconsistencies(conn)
    assert any(f"Booking {ticket.pnr} (CONFIRMED) holds 0 seat number(s) but should hold 2" in p
               for p in problems)


def test_checker_reports_a_cancelled_booking_that_still_holds_seats(conn):
    ticket = book(conn, 0, 1)
    conn.execute("UPDATE bookings SET status = 'CANCELLED' WHERE pnr = ?", (ticket.pnr,))
    problems = find_inconsistencies(conn)
    assert any("(CANCELLED) holds 1 seat number(s) but should hold 0" in p for p in problems)
    assert any("should be free" in p for p in problems)      # the count was never given back


def test_checker_reports_a_seat_number_above_the_class_size(conn):
    ticket = book(conn, 0, 1)
    conn.execute("UPDATE seat_allocations SET seat_number = 99 WHERE pnr = ?", (ticket.pnr,))
    assert any("holds seat 99 but the class has only 4 seats" in p
               for p in find_inconsistencies(conn))


# ------------------------------------------------------ a long random history

def test_counts_stay_consistent_through_two_hundred_random_bookings_and_cancellations():
    rng = random.Random(2026)
    conn = storage.connect(":memory:")
    storage.add_train(conn, Train("T1", "One", "A", "B", "10:00", tuple(range(7))),
                      [SeatClass("T1", "CC", 6, 100.0), SeatClass("T1", "SL", 3, 50.0)])
    storage.add_train(conn, Train("T2", "Two", "B", "C", "11:00", tuple(range(7))),
                      [SeatClass("T2", "SL", 4, 60.0)])
    for i in range(5):
        storage.add_passenger(conn, Passenger(f"p{i}@x.com", f"P{i}", "salt$hash"))
    options = [("T1", "CC"), ("T1", "SL"), ("T2", "SL")]
    held, booked, refused, cancelled = [], 0, 0, 0

    for step in range(200):
        if held and rng.random() < 0.4:
            cancel_booking(conn, held.pop(rng.randrange(len(held))).pnr, now=EARLY)
            cancelled += 1
        else:
            train, seat_class = rng.choice(options)
            day = DAY + timedelta(days=rng.randrange(2))
            try:
                held.append(book(conn, rng.randrange(5), rng.randint(1, 3), day, train, seat_class))
                booked += 1
            except BookingError:
                refused += 1
        assert find_inconsistencies(conn) == [], f"inconsistent after step {step}"

    assert booked > 20 and refused > 5 and cancelled > 20      # the run really did all three
    conn.close()


# --------------------------------------------- visible straight after cancelling

def test_another_open_connection_sees_the_cancelled_seat_straight_away(tmp_path):
    path = str(tmp_path / "visible.db")
    make_db(path, total_seats=2)
    owner, other = storage.connect(path), storage.connect(path)
    ticket = book(owner, 0, 2)                                        # class is now full

    assert availability.check_availability(other, "T1", DAY, "CC", TODAY).free_seats == 0
    with pytest.raises(BookingError, match="No seats available"):
        book(other, 1)

    cancel_booking(owner, ticket.pnr, now=EARLY)

    # the other connection was already open and is not reopened or refreshed
    assert availability.check_availability(other, "T1", DAY, "CC", TODAY).free_seats == 2
    assert book(other, 1, 2).seat_numbers == (1, 2)                   # and the seats can be booked
    owner.close()
    other.close()


# ---------------------------------------------------- the lost-seat bug (fixed)

def test_two_cancellations_at_once_never_lose_a_seat_from_the_count(tmp_path):
    """Forces the bad timing: cancellation 1 holds the database while cancellation 2 starts.

    Before the fix, cancellation 2 read the old seat count first and then wrote
    over cancellation 1's update, leaving a free seat uncounted.
    """
    path = str(tmp_path / "lost.db")
    make_db(path, total_seats=2)
    setup = storage.connect(path)
    x, y = book(setup, 0, 1), book(setup, 1, 1)                       # class is full
    setup.close()

    first = storage.connect(path)
    first.execute("BEGIN IMMEDIATE")                                  # cancellation 1 in progress
    done, started = {}, threading.Event()

    def second_cancellation():
        c = storage.connect(path)
        started.set()
        try:
            cancel_booking(c, y.pnr, now=EARLY)
            done["ok"] = True
        finally:
            c.close()

    thread = threading.Thread(target=second_cancellation)
    thread.start()
    started.wait()
    time.sleep(0.5)                                                   # it reaches the lock and waits
    storage.apply_cancellation(first, x.pnr)                          # cancellation 1 finishes
    first.close()
    thread.join(timeout=10)

    check = storage.connect(path)
    assert done.get("ok") and free(check) == 2                        # both seats counted as free
    assert find_inconsistencies(check) == []
    check.close()


@pytest.mark.parametrize("round_number", range(3))
def test_four_cancellations_at_once_give_all_four_seats_back(tmp_path, round_number):
    path = str(tmp_path / f"four{round_number}.db")
    make_db(path, total_seats=4)
    setup = storage.connect(path)
    held = [book(setup, i, 1) for i in range(4)]
    setup.close()

    run_together(path, [lambda c, t=t: cancel_booking(c, t.pnr, now=EARLY) for t in held])

    check = storage.connect(path)
    assert free(check) == 4 and find_inconsistencies(check) == []
    check.close()


def test_booking_and_cancelling_at_the_same_time_keeps_counts_and_seats_in_step(tmp_path):
    path = str(tmp_path / "churn.db")
    make_db(path, total_seats=4)
    setup = storage.connect(path)
    held = [book(setup, i, 1) for i in range(4)]                      # class is full
    setup.close()

    jobs = [lambda c, t=t: cancel_booking(c, t.pnr, now=EARLY) for t in held[:2]]
    jobs += [lambda c, i=i: book(c, i) for i in range(4, 8)]          # four others want a seat

    run_together(path, jobs)

    check = storage.connect(path)
    assert find_inconsistencies(check) == []
    assert 0 <= free(check) <= 4
    seats = [r[0] for r in check.execute("SELECT seat_number FROM seat_allocations")]
    assert len(seats) == len(set(seats))                              # no seat held twice
    check.close()

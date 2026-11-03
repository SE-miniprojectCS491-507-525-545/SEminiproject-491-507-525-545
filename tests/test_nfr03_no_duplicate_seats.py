"""NFR-03: the same seat is never given to two passengers.

These tests use real database files and several threads, each with its own
connection, so the bookings really do compete at the same moment.
"""
import threading
import time
from datetime import date

import pytest

from railway import storage
from railway.booking import BookingError, book_ticket
from railway.models import Passenger, SeatClass, Traveller, Train

DAY = date(2026, 11, 9)
TODAY = date(2026, 10, 26)


def make_db(path, total_seats, people):
    conn = storage.connect(path)
    storage.add_train(conn, Train("T1", "Test Express", "A", "B", "10:00", tuple(range(7))),
                      [SeatClass("T1", "CC", total_seats, 100.0)])
    for i in range(people):
        storage.add_passenger(conn, Passenger(f"p{i}@x.com", f"P{i}", "salt$hash"))
    conn.close()


def travellers(n):
    return [Traveller(f"Person {i}", 30, "F") for i in range(1, n + 1)]


def run_together(path, jobs):
    """Run every job in its own thread with its own connection, starting together.

    Each job is job(conn) and returns a value. Returns a list of
    ("ok", value) or ("refused", message); any other error fails the test.
    """
    results, problems = [None] * len(jobs), []
    barrier = threading.Barrier(len(jobs))

    def worker(index, job):
        conn = storage.connect(path)
        try:
            barrier.wait()
            try:
                results[index] = ("ok", job(conn))
            except BookingError as exc:
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


def book_job(index, seats=1):
    return lambda conn: book_ticket(conn, f"p{index}@x.com", "T1", DAY, "CC",
                                    travellers(seats), today=TODAY)


def seat_report(path):
    """(seat numbers in use, free count, highest seat number) read straight from the database."""
    conn = storage.connect(path)
    seats = [r[0] for r in conn.execute(
        "SELECT seat_number FROM seat_allocations "
        "WHERE train_number = 'T1' AND travel_date = ? AND seat_class = 'CC'", (DAY.isoformat(),))]
    free = storage.get_availability(conn, "T1", DAY, "CC")
    conn.close()
    return seats, free


def test_many_people_booking_a_small_class_at_once(tmp_path):
    path = str(tmp_path / "many.db")
    make_db(path, total_seats=5, people=12)

    results = run_together(path, [book_job(i) for i in range(12)])

    won = [r for kind, r in results if kind == "ok"]
    refused = [r for kind, r in results if kind == "refused"]
    assert len(won) == 5 and len(refused) == 7
    assert all("No seats available" in message for message in refused)
    seats, free = seat_report(path)
    assert sorted(seats) == [1, 2, 3, 4, 5]          # every seat used once, none twice
    assert free == 0
    assert len({t.pnr for t in won}) == 5            # five different PNRs


def test_bookings_of_different_sizes_competing_for_seats(tmp_path):
    path = str(tmp_path / "sizes.db")
    make_db(path, total_seats=12, people=10)

    results = run_together(path, [book_job(i, seats=2) for i in range(10)])

    assert sum(kind == "ok" for kind, _ in results) == 6
    seats, free = seat_report(path)
    assert len(seats) == len(set(seats)) == 12
    assert max(seats) <= 12 and free == 0


def test_one_big_booking_cannot_take_seats_another_booking_already_holds(tmp_path):
    path = str(tmp_path / "big.db")
    make_db(path, total_seats=6, people=3)

    results = run_together(path, [book_job(0, 4), book_job(1, 4), book_job(2, 4)])

    assert sum(kind == "ok" for kind, _ in results) == 1       # only one group of 4 fits in 6
    refused = [r for kind, r in results if kind == "refused"]
    assert all("Only 2 seat(s) left" in m for m in refused)
    seats, free = seat_report(path)
    assert len(seats) == len(set(seats)) == 4 and free == 2


@pytest.mark.parametrize("round_number", range(3))
def test_the_last_seat_goes_to_exactly_one_person_every_time(tmp_path, round_number):
    path = str(tmp_path / f"last{round_number}.db")
    make_db(path, total_seats=1, people=2)

    results = run_together(path, [book_job(0), book_job(1)])

    assert sorted(kind for kind, _ in results) == ["ok", "refused"]
    assert "No seats available" in next(r for kind, r in results if kind == "refused")
    assert seat_report(path) == ([1], 0)


def test_a_booking_that_starts_while_another_is_in_progress_waits_for_it(tmp_path):
    """Forces the bad timing: booking 1 holds the database while booking 2 starts."""
    path = str(tmp_path / "wait.db")
    make_db(path, total_seats=1, people=2)

    first = storage.connect(path)
    first.execute("BEGIN IMMEDIATE")              # booking 1 is now "in progress"

    outcome, started = {}, threading.Event()

    def second_booking():
        conn = storage.connect(path)
        started.set()
        try:
            outcome["result"] = ("ok", book_ticket(conn, "p1@x.com", "T1", DAY, "CC",
                                                   travellers(1), today=TODAY))
        except BookingError as exc:
            outcome["result"] = ("refused", str(exc))
        finally:
            conn.close()

    thread = threading.Thread(target=second_booking)
    thread.start()
    started.wait()
    time.sleep(0.5)                               # booking 2 reaches the lock and has to wait
    assert "result" not in outcome

    storage.book_seats(first, "1000000001", "p0@x.com", "T1", DAY, "CC",
                       [Traveller("Asha Rao", 30, "F")])      # booking 1 finishes
    first.close()
    thread.join(timeout=10)

    kind, message = outcome["result"]
    assert kind == "refused" and "No seats available" in message
    assert seat_report(path) == ([1], 0)


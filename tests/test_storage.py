from datetime import date, datetime

import pytest

from railway import storage
from railway.cancellation import CANCELLED, cancel_ticket
from railway.models import Booking, Passenger, SeatClass, Traveller, Train
from railway.storage import StorageError

TRAVEL = date(2026, 11, 2)


@pytest.fixture
def conn():
    c = storage.connect(":memory:")
    yield c
    c.close()


@pytest.fixture
def train():
    return Train("12627", "Karnataka Express", "Bengaluru", "Delhi", "19:20", (0, 2, 4))


@pytest.fixture
def seeded(conn, train):
    """A DB with one train, two classes, one passenger and availability."""
    storage.add_train(conn, train, [
        SeatClass("12627", "3AC", 60, 1500.0),
        SeatClass("12627", "SL", 120, 600.0),
    ])
    storage.add_passenger(conn, Passenger("a@x.com", "Asha", "salt$hash"))
    storage.set_availability(conn, "12627", TRAVEL, "3AC", 10)
    return conn


def make_booking(pnr="PNR1001", **kw):
    fields = dict(pnr=pnr, passenger_email="a@x.com", train_number="12627",
                  travel_date=TRAVEL, seat_class="3AC", passengers=2, fare=3000.0)
    fields.update(kw)
    return Booking(**fields)


# --- schema / connection ---

def test_all_tables_are_created(conn):
    names = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"trains", "seat_classes", "availability", "passengers",
            "bookings", "travellers", "seat_allocations"} <= names


def test_foreign_keys_are_switched_on(conn):
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


# --- trains ---

def test_train_round_trip_keeps_fields_and_types(conn, train):
    storage.add_train(conn, train)
    assert storage.get_train(conn, "12627") == train
    assert isinstance(storage.get_train(conn, "12627").runs_on, tuple)


def test_missing_train_returns_none(conn):
    assert storage.get_train(conn, "00000") is None


def test_duplicate_train_number_is_rejected(conn, train):
    storage.add_train(conn, train)
    with pytest.raises(StorageError):
        storage.add_train(conn, train)


def test_list_trains_is_sorted_by_number(conn, train):
    storage.add_train(conn, Train("20000", "B", "X", "Y", "08:00", (1,)))
    storage.add_train(conn, train)
    assert [t.number for t in storage.list_trains(conn)] == ["12627", "20000"]


def test_seat_classes_are_saved_with_the_train(seeded):
    classes = storage.get_seat_classes(seeded, "12627")
    assert [(c.seat_class, c.total_seats, c.fare) for c in classes] == [
        ("3AC", 60, 1500.0), ("SL", 120, 600.0)]


def test_train_and_classes_are_all_or_nothing(conn, train):
    duplicate = SeatClass("12627", "3AC", 60, 1500.0)
    with pytest.raises(StorageError):
        storage.add_train(conn, train, [duplicate, duplicate])
    assert storage.get_train(conn, "12627") is None


# --- availability ---

def test_availability_set_and_get(seeded):
    assert storage.get_availability(seeded, "12627", TRAVEL, "3AC") == 10


def test_availability_can_be_updated(seeded):
    storage.set_availability(seeded, "12627", TRAVEL, "3AC", 7)
    assert storage.get_availability(seeded, "12627", TRAVEL, "3AC") == 7


def test_unrecorded_availability_is_none(seeded):
    assert storage.get_availability(seeded, "12627", TRAVEL, "SL") is None


def test_negative_free_seats_are_rejected(seeded):
    with pytest.raises(StorageError):
        storage.set_availability(seeded, "12627", TRAVEL, "3AC", -1)


def test_availability_for_unknown_class_is_rejected(seeded):
    with pytest.raises(StorageError):
        storage.set_availability(seeded, "12627", TRAVEL, "1AC", 5)


def test_load_availability_uses_the_dict_shape_cancellation_expects(seeded):
    assert storage.load_availability(seeded) == {("12627", TRAVEL, "3AC"): 10}


def test_save_availability_writes_a_dict_back(seeded):
    storage.save_availability(seeded, {("12627", TRAVEL, "3AC"): 4,
                                       ("12627", TRAVEL, "SL"): 9})
    assert storage.get_availability(seeded, "12627", TRAVEL, "SL") == 9
    assert storage.get_availability(seeded, "12627", TRAVEL, "3AC") == 4


# --- passengers ---

def test_passenger_round_trip(seeded):
    assert storage.get_passenger(seeded, "a@x.com") == Passenger(
        "a@x.com", "Asha", "salt$hash", "passenger")


def test_missing_passenger_returns_none(conn):
    assert storage.get_passenger(conn, "nobody@x.com") is None


def test_duplicate_email_is_rejected(seeded):
    with pytest.raises(StorageError):
        storage.add_passenger(seeded, Passenger("a@x.com", "Other", "h"))


def test_invalid_role_is_rejected(conn):
    with pytest.raises(StorageError):
        storage.add_passenger(conn, Passenger("b@x.com", "B", "h", role="superuser"))


def test_load_passengers_is_keyed_by_email(seeded):
    assert list(storage.load_passengers(seeded)) == ["a@x.com"]


# --- bookings ---

def test_booking_round_trip_gives_back_a_real_date(seeded):
    storage.add_booking(seeded, make_booking())
    got = storage.get_booking(seeded, "PNR1001")
    assert got == make_booking()
    assert got.travel_date == TRAVEL and isinstance(got.travel_date, date)


def test_missing_booking_returns_none(conn):
    assert storage.get_booking(conn, "NOPE") is None


def test_travellers_are_saved_in_order(seeded):
    people = [Traveller("Asha", 30, "F"), Traveller("Ravi", 8, "M")]
    storage.add_booking(seeded, make_booking(), people)
    assert storage.get_travellers(seeded, "PNR1001") == people


def test_booking_for_unknown_train_is_rejected(seeded):
    with pytest.raises(StorageError):
        storage.add_booking(seeded, make_booking(train_number="99999"))


def test_booking_for_unknown_passenger_is_rejected(seeded):
    with pytest.raises(StorageError):
        storage.add_booking(seeded, make_booking(passenger_email="ghost@x.com"))


def test_booking_of_more_than_six_passengers_is_rejected(seeded):
    with pytest.raises(StorageError):
        storage.add_booking(seeded, make_booking(passengers=7))


def test_traveller_with_invalid_age_rolls_back_the_booking(seeded):
    with pytest.raises(StorageError):
        storage.add_booking(seeded, make_booking(), [Traveller("Baby", 0, "F")])
    assert storage.get_booking(seeded, "PNR1001") is None


def test_list_bookings_can_filter_by_passenger(seeded):
    storage.add_passenger(seeded, Passenger("b@x.com", "Bina", "h"))
    storage.add_booking(seeded, make_booking("PNR1001"))
    storage.add_booking(seeded, make_booking("PNR1002", passenger_email="b@x.com"))
    assert [b.pnr for b in storage.list_bookings(seeded)] == ["PNR1001", "PNR1002"]
    assert [b.pnr for b in storage.list_bookings(seeded, "b@x.com")] == ["PNR1002"]


def test_update_booking_status(seeded):
    storage.add_booking(seeded, make_booking())
    storage.update_booking_status(seeded, "PNR1001", CANCELLED)
    assert storage.get_booking(seeded, "PNR1001").status == CANCELLED


def test_update_status_of_unknown_booking_is_rejected(seeded):
    with pytest.raises(StorageError):
        storage.update_booking_status(seeded, "NOPE", CANCELLED)


def test_invalid_status_is_rejected(seeded):
    storage.add_booking(seeded, make_booking())
    with pytest.raises(StorageError):
        storage.update_booking_status(seeded, "PNR1001", "MAYBE")


# --- seat allocation (NFR-03) ---

def test_same_seat_cannot_be_given_to_two_bookings(seeded):
    storage.add_booking(seeded, make_booking("PNR1001"))
    storage.add_booking(seeded, make_booking("PNR1002"))
    storage.add_seat_allocation(seeded, "PNR1001", "12627", TRAVEL, "3AC", 14)
    with pytest.raises(StorageError):
        storage.add_seat_allocation(seeded, "PNR1002", "12627", TRAVEL, "3AC", 14)


def test_same_seat_number_is_fine_on_another_date_or_class(seeded):
    storage.add_booking(seeded, make_booking("PNR1001"))
    storage.add_seat_allocation(seeded, "PNR1001", "12627", TRAVEL, "3AC", 14)
    storage.add_seat_allocation(seeded, "PNR1001", "12627", date(2026, 11, 4), "3AC", 14)
    storage.add_seat_allocation(seeded, "PNR1001", "12627", TRAVEL, "SL", 14)
    assert storage.get_seat_numbers(seeded, "PNR1001") == [14, 14, 14]


def test_deleting_allocations_frees_the_seats(seeded):
    storage.add_booking(seeded, make_booking("PNR1001"))
    storage.add_booking(seeded, make_booking("PNR1002"))
    storage.add_seat_allocation(seeded, "PNR1001", "12627", TRAVEL, "3AC", 14)
    storage.delete_seat_allocations(seeded, "PNR1001")
    assert storage.get_seat_numbers(seeded, "PNR1001") == []
    storage.add_seat_allocation(seeded, "PNR1002", "12627", TRAVEL, "3AC", 14)


# --- works with existing code ---

def test_cancel_ticket_works_on_data_loaded_from_the_database(seeded):
    storage.add_booking(seeded, make_booking(passengers=2))
    bookings = storage.load_bookings(seeded)
    availability = storage.load_availability(seeded)

    trains = storage.list_trains(seeded)
    result = cancel_ticket("PNR1001", bookings, availability, trains,
                           now=datetime(2026, 10, 21, 10, 0))
    storage.update_booking_status(seeded, "PNR1001", bookings["PNR1001"].status)
    storage.save_availability(seeded, availability)

    assert result.seats_released == 2
    assert storage.get_booking(seeded, "PNR1001").status == CANCELLED
    assert storage.get_availability(seeded, "12627", TRAVEL, "3AC") == 12


# --- persistence (NFR-05) ---

def test_data_survives_closing_and_reopening_the_database(tmp_path, train):
    path = str(tmp_path / "railway.db")
    first = storage.connect(path)
    storage.add_train(first, train, [SeatClass("12627", "3AC", 60, 1500.0)])
    storage.set_availability(first, "12627", TRAVEL, "3AC", 10)
    first.close()

    second = storage.connect(path)
    assert storage.get_train(second, "12627") == train
    assert storage.get_availability(second, "12627", TRAVEL, "3AC") == 10
    second.close()


# --- Tanisha can swap her temporary Train for the shared one ---

def test_search_works_with_the_shared_train_model(conn, train):
    from railway.search import search_trains
    storage.add_train(conn, train)
    found = search_trains("Bengaluru", "Delhi", TRAVEL, storage.list_trains(conn),
                          ["Bengaluru", "Delhi"], today=date(2026, 10, 21))
    assert [t.number for t in found] == ["12627"]
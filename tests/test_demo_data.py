import pytest

from railway import storage
from railway.auth import login
from railway.demo_data import DEMO_EMAIL, DEMO_PASSWORD, seed_demo_data


@pytest.fixture
def conn():
    c = storage.connect(":memory:")
    yield c
    c.close()


def test_seed_adds_trains_classes_and_demo_user(conn):
    assert seed_demo_data(conn) is True
    assert [t.number for t in storage.list_trains(conn)] == ["12627", "12628", "20601"]
    assert [c.seat_class for c in storage.get_seat_classes(conn, "12627")] == ["3AC", "SL"]
    assert DEMO_EMAIL in storage.load_passengers(conn)


def test_seed_can_run_twice_without_duplicating(conn):
    seed_demo_data(conn)
    assert seed_demo_data(conn) is False
    assert len(storage.list_trains(conn)) == 3


def test_demo_user_can_log_in_and_password_is_not_stored_in_plain_text(conn):
    seed_demo_data(conn)
    passengers = storage.load_passengers(conn)
    assert passengers[DEMO_EMAIL].password_hash != DEMO_PASSWORD
    assert login(DEMO_EMAIL, DEMO_PASSWORD, passengers, {})
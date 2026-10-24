"""Sample data so the demo has something to search and book (TASK-06).

Run through the CLI with:  python -m railway --seed
"""
from railway import storage
from railway.models import SeatClass, Train
from railway.registration import register_passenger

EVERY_DAY = tuple(range(7))

DEMO_EMAIL = "demo@railway.com"
DEMO_PASSWORD = "demo12345"

_TRAINS = [
    (Train("12627", "Karnataka Express", "Bengaluru", "Delhi", "19:20", EVERY_DAY),
     [("3AC", 60, 1500.0), ("SL", 120, 600.0)]),
    (Train("12628", "Delhi-Bengaluru Express", "Delhi", "Bengaluru", "08:00", EVERY_DAY),
     [("3AC", 40, 1550.0), ("SL", 100, 650.0)]),
    (Train("20601", "Bengaluru-Mysuru Intercity", "Bengaluru", "Mysuru", "08:30", EVERY_DAY),
     [("CC", 60, 380.0), ("SL", 90, 160.0)]),
]


def seed_demo_data(conn):
    """Add the sample trains and a demo account. Safe to run more than once."""
    if storage.list_trains(conn):
        return False
    for train, classes in _TRAINS:
        storage.add_train(conn, train, [
            SeatClass(train.number, name, seats, fare) for name, seats, fare in classes
        ])
    passengers = storage.load_passengers(conn)
    if DEMO_EMAIL not in passengers:
        storage.add_passenger(
            conn, register_passenger("Demo User", DEMO_EMAIL, DEMO_PASSWORD, passengers))
    return True
"""Sample data and separate passenger/admin accounts for local demonstrations.

Run through the CLI with: python -m railway --seed
Demo credentials are for local demonstrations only; change them before any
shared or deployed use.
"""
from railway import storage
from railway.models import ROLE_ADMIN, Passenger, SeatClass, Train
from railway.registration import register_passenger

EVERY_DAY = tuple(range(7))

DEMO_EMAIL = "demo@railway.com"
DEMO_PASSWORD = "demo12345"  # nosec B105 - public local-demo credential only
DEMO_ADMIN_EMAIL = "admin@railway.com"
DEMO_ADMIN_PASSWORD = "Admin12345"  # nosec B105 - public local-demo credential only

_TRAINS = [
    (Train("12627", "Karnataka Express", "Bengaluru", "Delhi", "19:20", EVERY_DAY),
     [("3AC", 60, 1500.0), ("SL", 120, 600.0)]),
    (Train("12628", "Delhi-Bengaluru Express", "Delhi", "Bengaluru", "08:00", EVERY_DAY),
     [("3AC", 40, 1550.0), ("SL", 100, 650.0)]),
    (Train("20601", "Bengaluru-Mysuru Intercity", "Bengaluru", "Mysuru", "08:30", EVERY_DAY),
     [("CC", 60, 380.0), ("SL", 90, 160.0)]),
]


def seed_demo_data(conn):
    """Ensure sample trains and separate demo passenger/admin accounts exist."""
    changed = False
    if not storage.list_trains(conn):
        for train, classes in _TRAINS:
            storage.add_train(conn, train, [
                SeatClass(train.number, name, seats, fare)
                for name, seats, fare in classes
            ])
        changed = True

    passengers = storage.load_passengers(conn)
    if DEMO_EMAIL not in passengers:
        storage.add_passenger(
            conn,
            register_passenger("Demo User", DEMO_EMAIL, DEMO_PASSWORD, passengers),
        )
        changed = True

    passengers = storage.load_passengers(conn)
    if DEMO_ADMIN_EMAIL not in passengers:
        admin = register_passenger(
            "Demo Administrator", DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD, passengers
        )
        storage.add_passenger(
            conn, Passenger(admin.email, admin.name, admin.password_hash, ROLE_ADMIN)
        )
        changed = True

    return changed

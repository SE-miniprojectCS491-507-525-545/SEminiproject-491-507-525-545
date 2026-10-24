from datetime import date, datetime

import pytest

from railway import storage
from railway.cli import App
from railway.demo_data import seed_demo_data

CLI_TODAY = date(2026, 10, 24)
CLI_NOW = datetime(2026, 10, 24, 10, 0)


@pytest.fixture
def fast_passwords(monkeypatch):
    """Swap the deliberately slow password hashing for a cheap stand-in.

    Registration and login hash a password on every call, which takes a
    noticeable fraction of a second each time. The CLI tests are about the menu
    flow, not about hashing (that is covered by test_security.py and
    test_auth.py), so they use this stand-in to keep the suite fast.
    """
    monkeypatch.setattr("railway.registration.hash_password", lambda p: "test$" + p)
    monkeypatch.setattr("railway.auth.verify_password", lambda p, h: h == "test$" + p)


@pytest.fixture
def cli_conn(fast_passwords):
    """In-memory database with the demo trains and the demo account."""
    conn = storage.connect(":memory:")
    seed_demo_data(conn)
    yield conn
    conn.close()


@pytest.fixture
def run_cli(cli_conn):
    """run_cli(["1", "Asha", ...]) types those answers into the CLI and
    returns everything it printed as one string."""
    def run(inputs, now=CLI_NOW, book=None):
        feed = iter(inputs)
        out = []
        App(cli_conn, ask=lambda prompt: next(feed), say=out.append,
            today=CLI_TODAY, now=now, book_ticket=book).run()
        return "\n".join(out)
    return run
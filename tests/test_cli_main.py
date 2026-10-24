from railway import storage
from railway.cli import main


def test_main_seeds_and_runs_the_menu(tmp_path):
    db = str(tmp_path / "railway.db")
    out = []
    main(["--db", db, "--seed"], ask=lambda prompt: "0", say=out.append)
    assert any("Demo login: demo@railway.com / demo12345" in line for line in out)
    assert "Goodbye." in out

    conn = storage.connect(db)          # data was written to the file
    assert len(storage.list_trains(conn)) == 3
    conn.close()


def test_main_without_seed_starts_empty(tmp_path):
    db = str(tmp_path / "empty.db")
    main(["--db", db], ask=lambda prompt: "0", say=lambda line: None)
    conn = storage.connect(db)
    assert storage.list_trains(conn) == []
    conn.close()
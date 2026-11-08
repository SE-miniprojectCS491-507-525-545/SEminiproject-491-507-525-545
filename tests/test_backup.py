import sqlite3

import pytest

from railway.backup import BackupError, create_backup, restore_backup


def _make_db(path, value):
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE sample (value TEXT)")
        conn.execute("INSERT INTO sample VALUES (?)", (value,))


def test_create_backup_produces_valid_copy(tmp_path):
    source = tmp_path / "source.db"
    backup = tmp_path / "backup.db"
    _make_db(source, "original")
    assert create_backup(source, backup) == str(backup.resolve())
    with sqlite3.connect(backup) as conn:
        assert conn.execute("SELECT value FROM sample").fetchone()[0] == "original"


def test_restore_backup_replaces_destination_with_valid_copy(tmp_path):
    backup = tmp_path / "backup.db"
    destination = tmp_path / "restored.db"
    _make_db(backup, "saved")
    _make_db(destination, "old")
    restore_backup(backup, destination)
    with sqlite3.connect(destination) as conn:
        assert conn.execute("SELECT value FROM sample").fetchone()[0] == "saved"


def test_backup_refuses_same_source_and_destination(tmp_path):
    source = tmp_path / "source.db"
    _make_db(source, "data")
    with pytest.raises(BackupError, match="differ"):
        create_backup(source, source)


def test_restore_refuses_same_source_and_destination(tmp_path):
    source = tmp_path / "source.db"
    _make_db(source, "data")
    with pytest.raises(BackupError, match="differ"):
        restore_backup(source, source)


def test_restore_rejects_invalid_backup_without_changing_destination(tmp_path):
    backup = tmp_path / "invalid.db"
    backup.write_text("not a sqlite database")
    destination = tmp_path / "destination.db"
    _make_db(destination, "keep")
    with pytest.raises(BackupError):
        restore_backup(backup, destination)
    with sqlite3.connect(destination) as conn:
        assert conn.execute("SELECT value FROM sample").fetchone()[0] == "keep"

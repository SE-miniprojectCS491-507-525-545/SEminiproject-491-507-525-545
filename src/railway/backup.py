"""Safe SQLite database backup and restore helpers."""
import os
import sqlite3
import tempfile
from pathlib import Path


class BackupError(ValueError):
    """Raised when a database backup or restore cannot be completed."""


def _validate_database(path):
    try:
        with sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True) as conn:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if result is None or result[0] != "ok":
                raise BackupError("Database failed SQLite integrity validation.")
    except sqlite3.Error as exc:
        raise BackupError(f"Could not validate SQLite database: {exc}") from exc


def create_backup(source_path, backup_path):
    """Create a consistent SQLite backup using SQLite's online backup API."""
    source = Path(source_path).resolve()
    destination = Path(backup_path).resolve()
    if source == destination:
        raise BackupError("Backup destination must differ from the source database.")
    if not source.is_file():
        raise BackupError("Source database does not exist.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        fd, temporary = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
        )
        os.close(fd)
        with sqlite3.connect(str(source)) as src, sqlite3.connect(temporary) as dst:
            src.backup(dst)
        _validate_database(temporary)
        os.replace(temporary, destination)
        return str(destination)
    except (OSError, sqlite3.Error) as exc:
        raise BackupError(f"Could not create database backup: {exc}") from exc
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def restore_backup(backup_path, destination_path):
    """Validate a backup, then atomically restore it to a separate database file.

    The destination is never the source backup. An existing destination is
    replaced atomically only after the backup has passed integrity checking.
    """
    source = Path(backup_path).resolve()
    destination = Path(destination_path).resolve()
    if source == destination:
        raise BackupError("Restore destination must differ from the backup.")
    if not source.is_file():
        raise BackupError("Backup file does not exist.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        _validate_database(source)
        fd, temporary = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".restore", dir=destination.parent
        )
        os.close(fd)
        with sqlite3.connect(str(source)) as src, sqlite3.connect(temporary) as dst:
            src.backup(dst)
        _validate_database(temporary)
        os.replace(temporary, destination)
        return str(destination)
    except (OSError, sqlite3.Error) as exc:
        raise BackupError(f"Could not restore database backup: {exc}") from exc
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)

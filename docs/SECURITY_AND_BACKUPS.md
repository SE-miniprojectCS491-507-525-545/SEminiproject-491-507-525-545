# Demo accounts, sessions, and database backups

## Demo accounts

Run the application with `python -m railway --seed` to create sample trains
and two separate demo accounts:

- Passenger: `demo@railway.com` / `demo12345`
- Administrator: `railway-admin-demo@railway.com` / `Admin12345`

These credentials are intentionally convenient for local demonstrations only.
Do not use them in a shared or deployed environment. Change the passwords or
remove the demo accounts before deployment. Normal passenger registration
always creates a passenger role; it does not accept a role parameter.

## Session expiration

CLI sessions expire after 30 minutes by default. Set
`RAILWAY_SESSION_TTL_SECONDS` to a positive integer to change the timeout.
For example, `RAILWAY_SESSION_TTL_SECONDS=900` sets a 15-minute timeout.
Sessions are in memory and are cleared when the application process exits.

## SQLite backup and restore

Use the helper functions in `railway.backup`:

```python
from railway.backup import create_backup, restore_backup

create_backup("railway.db", "backups/railway-backup.db")
restore_backup("backups/railway-backup.db", "railway-restored.db")
```

The backup helper uses SQLite's online backup API, validates the resulting
database, and writes through a temporary file before replacing the destination.
Restore validates the backup before writing and restores to a separate
destination path. Do not restore over a database currently in use; stop the
application first and restore to a separate file, then point the application
at that file with `--db` after checking it.

## CI security checks

GitHub Actions runs Bandit against the source tree, audits the development
dependency requirements with pip-audit, and runs the pytest coverage suite.

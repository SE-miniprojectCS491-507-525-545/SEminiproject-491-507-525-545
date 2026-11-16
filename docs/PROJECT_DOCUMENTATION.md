# Railway Reservation System — Project & Technical Documentation

> **Purpose:** This is the developer-facing reference for the implementation currently present in the repository. It describes the actual code structure, interfaces, data model, workflows, security controls, test evidence, measurable constraints and known documentation gaps.
>
> **Accuracy rule:** This document is based on the source tree on the repository's `main` branch at the time it was written. A feature being present in code does not, by itself, prove that its UI has been manually tested or that a requirement has passed acceptance testing. Historical test records are labelled as historical. Update this document when code, interfaces, requirements or test evidence change.

## 1. Project at a glance

The Railway Reservation System is a Python application for managing train journeys and reservations. It provides two user interfaces:

- **Streamlit web UI** in the repository-root `app.py`.
- **Command-line interface (CLI)** in `src/railway/cli.py`, launched through `python -m railway`.

Both interfaces use the Python application modules in `src/railway/`. Persistent application data is stored in SQLite. There is no separate REST server or HTTP JSON API in the current implementation.

### 1.1 Main capabilities in the current source

| Capability | Current implementation |
|---|---|
| Passenger registration | Implemented through `registration.py`, persisted in SQLite |
| Login and logout | Implemented through `auth.py`; sessions are held in application memory |
| Train search | Search by source, destination and travel date |
| Seat availability | Availability by train, travel date and class |
| Ticket booking | Booking for 1–6 travellers, PNR creation and seat-number allocation |
| Booking history | Passenger-specific booking list in Streamlit and CLI |
| PNR lookup | Booking details with ownership checks |
| Cancellation | Cancellation deadline, refund calculation, seat release |
| Administration | Add, update and deactivate trains; admin-only UI |
| Data persistence | SQLite storage layer and schema initialization |
| Backup and restore | SQLite online backup, integrity validation and atomic replacement helpers |
| Consistency diagnostics | Checks availability counts and seat-allocation consistency |

This table describes code presence. The evidence and outstanding test work are described in [Section 12](#12-testing-and-evidence).

## 2. Repository map

| Path | Responsibility |
|---|---|
| `app.py` | Streamlit frontend, page navigation, forms, user feedback and UI-level access gating |
| `src/railway/models.py` | Shared dataclasses and role/booking status constants |
| `src/railway/storage.py` | SQLite connection, schema, migrations, queries and transactional persistence |
| `src/railway/registration.py` | Registration validation and passenger creation |
| `src/railway/security.py` | Password hashing and verification |
| `src/railway/auth.py` | Login, logout, session tokens and expiry |
| `src/railway/access.py` | Administrator and booking-ownership checks |
| `src/railway/search.py` | Station extraction, search input validation and matching |
| `src/railway/availability.py` | Seat availability lookup and status calculation |
| `src/railway/seats.py` | Seat-number allocation algorithm |
| `src/railway/traveller_validation.py` | Traveller detail validation |
| `src/railway/booking.py` | Booking orchestration and ticket result formatting |
| `src/railway/pnr.py` | Unique 10-digit PNR generation |
| `src/railway/booking_views.py` | Booking detail lookup, formatting and authorization |
| `src/railway/cancellation.py` | Cancellation rules, deadlines and refund calculations |
| `src/railway/consistency.py` | Database consistency diagnostics |
| `src/railway/backup.py` | Validated SQLite backup and restore |
| `src/railway/perf.py` | Search timing helper and 5-second threshold predicate |
| `src/railway/dates.py` | Shared date parsing |
| `src/railway/search_help.py` | CLI search prompts and hints |
| `src/railway/demo_data.py` | Demonstration data and demo accounts |
| `src/railway/cli.py` | CLI workflow and command handlers |
| `src/railway/__main__.py` | Enables `python -m railway` |
| `tests/` | Automated unit, integration, storage and concurrency tests |
| `.github/workflows/ci.yml` | GitHub Actions checks |
| `requirements.txt` | Runtime dependency list |
| `requirements-dev.txt` | Development and test dependency list |
| `docs/` | Requirements, architecture, security, deviation and testing artefacts |

## 3. Technology stack and configuration

| Area | Technology / configuration | Evidence in repository |
|---|---|---|
| Language | Python | Application and test source |
| Web UI | Streamlit, constrained to `>=1.40,<2` | `requirements.txt`, `app.py` |
| Database | SQLite via Python's `sqlite3` | `src/railway/storage.py` |
| Automated tests | pytest | `requirements-dev.txt`, `tests/` |
| Coverage | pytest-cov | CI command |
| Static security scan | Bandit | CI command |
| Dependency vulnerability audit | pip-audit | CI command |
| CI runtime | Ubuntu runner, Python 3.12 | `.github/workflows/ci.yml` |

### 3.1 Install and run

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# Windows PowerShell: .venv\\Scripts\\Activate.ps1

python -m pip install -r requirements.txt
```

To run the Streamlit interface:

```bash
PYTHONPATH=src streamlit run app.py
```

To run the CLI:

```bash
PYTHONPATH=src python -m railway
```

To seed demonstration data through the CLI:

```bash
PYTHONPATH=src python -m railway --seed
```

On Windows PowerShell, set the source path first:

```powershell
$env:PYTHONPATH = "src"
streamlit run app.py
# or
python -m railway
```

Install development/test dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run tests:

```bash
PYTHONPATH=src python -m pytest
```

Run tests with a local coverage report:

```bash
PYTHONPATH=src python -m pytest --cov=src --cov-branch --cov-report=term-missing
```

### 3.2 Database location

The default database filename is `railway.db` in the repository root. It is created and initialized when `storage.connect()` is called. The location can be overridden using `RAILWAY_DB`.

macOS / Linux:

```bash
export RAILWAY_DB="/absolute/path/to/railway.db"
```

Windows PowerShell:

```powershell
$env:RAILWAY_DB = "C:\\path\\to\\railway.db"
```

The Streamlit entry point creates a database connection for the current script run and closes it in a `finally` block. It deliberately does not keep a live SQLite connection in Streamlit session state, because Streamlit may rerun the app on a different thread.

### 3.3 Session lifetime

The default session time-to-live (TTL) is **1,800 seconds (30 minutes)**. Set `RAILWAY_SESSION_TTL_SECONDS` to a positive integer to change it. Session state is in memory; a process restart clears active sessions. This is a demo/course application design, not a distributed production session service.

## 4. Architecture and application flow

### 4.1 Architecture overview

```text
             Passenger / Administrator
                       |
          +------------+------------+
          |                         |
     Streamlit UI                 CLI
       app.py             python -m railway
          |                         |
          +------------+------------+
                       |
             Application services
  +----------+----------+----------+----------+
  | Search   | Booking  | Auth     | Cancel   |
  | Avail.   | PNR      | Access   | Views    |
  +----------+----------+----------+----------+
                       |
                 Storage layer
                  storage.py
                       |
                    SQLite
  +---------+---------+----------+-------------+
  | trains  | classes | bookings | passengers  |
  | avail.  | travellers        | seat_alloc.  |
  +---------+---------+----------+-------------+

     Supporting services: security, validation,
     consistency checks, backup and performance helper
```

The UI and CLI are presentation layers. Business rules are primarily implemented in reusable Python modules. SQLite access is centralized in `storage.py`; service modules call its functions instead of building SQL in the UI.

### 4.2 Typical booking sequence

1. The passenger registers or logs in.
2. The frontend obtains train data from storage and calls the train search/availability services.
3. The passenger selects a train, travel date and class, and enters traveller details.
4. `booking.book_ticket()` validates the account, traveller information and availability.
5. A PNR is generated by `pnr.generate_pnr()`.
6. `storage.book_seats()` starts a write transaction, rechecks the seat count, allocates seat numbers, decreases availability and saves the booking, travellers and seat allocations together.
7. The UI or CLI shows the confirmation including PNR, train, date, class, seats and fare.

### 4.3 Typical cancellation sequence

1. The system obtains the booking and verifies that it exists and is still confirmed.
2. The booking's saved departure time is used when available, so a later train schedule edit does not change the historical cancellation calculation.
3. Cancellation is rejected when fewer than four hours remain before departure.
4. The refund is calculated using the documented fee slabs.
5. `storage.apply_cancellation()` atomically marks the booking cancelled, increases free seats without exceeding class capacity, and deletes the booking's seat-number allocations.

## 5. Frontend documentation

### 5.1 Streamlit UI

The frontend is a single Streamlit entry file, `app.py`, and is organized into functions:

| UI function | Purpose |
|---|---|
| `register(conn)` | Passenger registration form, including password confirmation |
| `login_screen(conn)` | Login form |
| `search_screen(conn)` | Search source/destination/date and show train and class availability |
| `availability_screen(conn)` | Show class capacity, free seats, fare and status |
| `booking_screen(conn, user)` | Booking form for one to six travellers and confirmation |
| `bookings_screen(conn, user)` | List the logged-in passenger's bookings |
| `pnr_screen(conn, user)` | Look up and display an authorized booking by PNR |
| `cancel_screen(conn, user)` | Calculate refund then ask for cancellation confirmation |
| `admin_screen(conn, user)` | Admin-only add, update and remove train tabs |
| `render_app(conn)` | Sidebar, session state and page dispatch |
| `main()` | Opens and closes the per-rerun SQLite connection |

The Streamlit session state stores the token, session mapping and pending cancellation details. The live SQLite connection is local to a run, not saved in session state.

### 5.2 CLI

The CLI is implemented by `railway.cli.App`. It provides menu options for account registration, login/logout, search, availability, booking, booking history, PNR lookup, cancellation and train administration. It uses injectable input/output functions to make CLI workflows testable.

### 5.3 Frontend limitations and boundaries

- The Streamlit UI uses Python directly; it is not a separate React/JavaScript frontend.
- No REST/HTTP API server is defined in the current repository.
- UI automation or a formal browser-based Streamlit test suite is not shown in the inspected test tree. Backend tests should not be represented as end-to-end browser tests.
- Authentication sessions are in process memory and are not shared across multiple application workers.

## 6. Backend services and interfaces

The project exposes **Python function interfaces**, not network endpoints. The table below documents the principal service entry points visible in the current source. The full function signatures and behavior remain authoritative in the source files.

| Module | Principal public functions / types | Purpose |
|---|---|---|
| `search.py` | `stations_of(trains)`, `validate_search(source, destination, travel_date, stations, today=None)`, `search_trains(...)`, `SearchError` | Validate and search direct train routes |
| `availability.py` | `check_availability(conn, train_number, travel_date, seat_class, today=None)`, `list_availability(...)`, `Availability`, `AvailabilityError` | Read availability by date and class |
| `registration.py` | `validate_registration(...)`, `register_passenger(...)`, `RegistrationError` | Validate and construct passenger accounts |
| `auth.py` | `login(email, password, passengers, sessions)`, `logout(token, sessions)`, `current_passenger(token, passengers, sessions)`, `SessionStore` | Authenticate users and validate sessions |
| `booking.py` | `book_ticket(conn, passenger_email, train_number, travel_date, seat_class, travellers, today=None)`, `format_ticket(ticket)`, `Ticket`, `BookingError` | Orchestrate booking and return ticket details |
| `pnr.py` | `generate_pnr(exists, pick=..., attempts=20)` | Generate unused PNR |
| `booking_views.py` | `view_booking(conn, pnr, passenger)`, `list_all_bookings(conn, passenger)`, formatters | Fetch authorized booking detail and admin list |
| `cancellation.py` | `validate_cancellation(...)`, `validate_deadline(...)`, `calculate_refund(...)`, `preview_refund(...)`, `cancel_booking(conn, pnr, now=None)` | Apply cancellation rules and database cancellation |
| `access.py` | `is_admin(...)`, `require_admin(...)`, `can_access_booking(...)`, `require_booking_access(...)` | Role and ownership checks |
| `storage.py` | `connect()`, `init_db(conn)`, train/passenger/booking CRUD and query helpers, `book_seats(...)`, `apply_cancellation(...)` | SQLite persistence and transaction boundary |
| `consistency.py` | `find_inconsistencies(conn)`, `is_consistent(conn)` | Detect seat-count and seat-allocation mismatches |
| `backup.py` | `create_backup(source_path, backup_path)`, `restore_backup(backup_path, destination_path)` | Create and validate database backup/restore |
| `perf.py` | `timed(function, *args, **kwargs)`, `within_limit(seconds, limit=5.0)` | Measure elapsed time and compare with NFR threshold |

### 6.1 Error handling

Service modules define domain-specific exceptions (usually subclasses of `ValueError`) such as `SearchError`, `AvailabilityError`, `BookingError`, `CancellationError`, `RegistrationError` and `BookingViewError`. The frontend catches expected validation/service errors and displays their messages. `storage.py` uses `StorageError` and `NotEnoughSeats` to communicate database and inventory failures.

### 6.2 Example service-level usage

Example only; run with the project installed/import path set and a seeded database:

```python
from railway import storage
from railway.search import search_trains, stations_of

conn = storage.connect()
try:
    trains = storage.list_trains(conn)
    stations = stations_of(trains)
    matches = search_trains(
        "Bengaluru", "Mysuru", "2026-12-02",
        trains, stations
    )
    for train in matches:
        print(train.number, train.name, train.departure)
finally:
    conn.close()
```

## 7. API specification — actual interface contract

### 7.1 Important distinction

The design documents refer to REST-style examples such as `POST /booking`. The current implementation does **not** start an HTTP server and has no registered `/booking`, `/cancellation`, `/login` or other REST routes. The actual interface is a set of Python functions called by the Streamlit UI and CLI.

The following tables are therefore the **current service/API contract**, not a claim that HTTP endpoints exist.

### 7.2 Search service

| Item | Contract |
|---|---|
| Entry point | `search_trains(source, destination, travel_date, trains, stations, today=None)` |
| Inputs | Source station, destination station, date, train collection, known station collection; optional reference date for deterministic tests |
| Success | List of matching Train objects |
| Validation | Required source/destination/date; known stations; source and destination differ; date is not in the past |
| Failure | `SearchError` with a user-readable explanation |

### 7.3 Availability service

| Item | Contract |
|---|---|
| Entry point | `check_availability(conn, train_number, travel_date, seat_class, today=None)` |
| Inputs | SQLite connection, train number, date, seat class |
| Success | `Availability` containing train, date, class, total seats, free seats and fare |
| Status | `AVAILABLE` when free seats > 0; otherwise `SOLD OUT` |
| Failure | `AvailabilityError` for invalid date, past date, unknown train, non-running day or invalid class |
| Initial inventory | If no availability row exists for a train/date/class, all configured class seats are treated as free |

### 7.4 Booking service

| Item | Contract |
|---|---|
| Entry point | `book_ticket(conn, passenger_email, train_number, travel_date, seat_class, travellers, today=None)` |
| Inputs | Connection, registered passenger email, train, date, class and traveller collection |
| Success | `Ticket` with PNR, train identity, date, class, travellers, allocated seat numbers, total fare and status |
| Constraints | Must be a registered passenger; traveller validation must pass; requested seats must be available; one booking is limited to six travellers |
| Failure | `BookingError` for login, validation, availability, storage or PNR failures |
| Database effect | Booking, traveller records, seat allocations and availability decrement are committed together |

### 7.5 Cancellation service

| Item | Contract |
|---|---|
| Entry point | `cancel_booking(conn, pnr, now=None)` |
| Inputs | Connection, PNR; optional current datetime for deterministic tests |
| Success | `CancellationResult` with PNR, seats released and refund amount |
| Constraints | Booking exists, is not already cancelled, and cancellation is made at least four hours before saved departure time |
| Refund rule | More than 24 hours: 10% fee; from 24 hours to the 4-hour limit: 50% fee |
| Database effect | Status update, free-seat increase and removal of seat allocations occur atomically |
| Failure | `CancellationError` for invalid booking, deadline, or storage problem |

### 7.6 Booking access service

| Item | Contract |
|---|---|
| Entry point | `view_booking(conn, pnr, passenger)` |
| Passenger access | A passenger can view only their own booking |
| Admin access | Administrator can view any booking |
| Failure behavior | Unknown PNR and another passenger's PNR produce the same not-found response |

### 7.7 Authentication service

| Item | Contract |
|---|---|
| Entry points | `login(email, password, passengers, sessions)`, `logout(token, sessions)`, `current_passenger(token, passengers, sessions)` |
| Login success | Returns a random session token |
| Login failure | Generic invalid email or password error |
| Session token | 16 random bytes encoded as 32 hexadecimal characters |
| Expiry | 1,800 seconds by default; configurable via `RAILWAY_SESSION_TTL_SECONDS` |
| Storage | In-memory session store; it is not a persistent token service |

### 7.8 Error and transport conventions

There is no HTTP status-code, JSON schema, request-header, CORS, authentication middleware or network transport contract because the current repository has no HTTP API. The Python function signatures and typed/result objects above are the current interface. A future REST API would need a separately designed and implemented transport layer.

## 8. Data model and database design

SQLite is initialized by `storage.connect()` / `storage.init_db()`. The schema uses primary keys, foreign keys and CHECK/UNIQUE constraints to protect important invariants.

### 8.1 Tables

| Table | Key fields and purpose |
|---|---|
| `trains` | Train number primary key; name, source, destination, departure, running weekdays and active flag |
| `seat_classes` | Composite primary key (train number, class); total seats and fare |
| `availability` | Composite key (train, date, class); free-seat count for one service date |
| `passengers` | Email primary key; name, password hash and role |
| `bookings` | PNR primary key; passenger, train, date, class, passenger count, total fare, status and departure snapshot |
| `travellers` | Auto-increment row ID; booking PNR, traveller name, age and gender |
| `seat_allocations` | Booking PNR, train, date, class and seat number; database uniqueness constraint prevents seat reuse on the same train/date/class |

### 8.2 Relationships

- One train has one or more seat classes.
- A seat class is identified by train number plus class name.
- Availability refers to a train/date/class combination.
- A passenger can own multiple bookings.
- A booking references one passenger and one train/date/class combination.
- A booking has traveller rows and allocated seat-number rows.
- Cancelling a booking removes its seat-allocation rows, allowing those seat numbers to be reused.

### 8.3 Important integrity rules in the schema

- Train number, passenger email and PNR are primary keys.
- Class capacity and fare cannot be negative.
- Free-seat counts cannot be negative.
- Booking passenger count must be between 1 and 6.
- Traveller age must be between 1 and 120.
- Booking status must be `CONFIRMED` or `CANCELLED`.
- Passenger role must be `passenger` or `admin`.
- A seat number must be at least 1.
- The UNIQUE constraint on (train number, travel date, class, seat number) prevents two bookings from holding the same seat.

### 8.4 Schema initialization and migration

The database schema is created with `CREATE TABLE IF NOT EXISTS`. `init_db()` also adds `trains.is_active` and `bookings.departure_at_booking` when missing, backfills the latter from train departure for existing booking rows, and removes a legacy trigger. These are lightweight in-place migrations, not a separate versioned migration framework.

## 9. Business rules and validation values

| Rule | Implemented value / behavior | Source |
|---|---|---|
| Maximum travellers per booking | 6 | `cli.py`, Streamlit booking form and DB CHECK |
| Minimum password length | 8 characters | `registration.py` |
| Password composition | At least one alphabetic character and one digit | `registration.py` |
| Traveller age | 1–120 inclusive | DB CHECK and traveller validation |
| PNR length | 10 digits, first digit cannot be zero | `pnr.py` |
| PNR generation attempts | Up to 20 candidates before failure | `pnr.py` |
| Session TTL | 1,800 seconds default | `auth.py` |
| Cancellation deadline | At least 4 hours before departure; exactly 4 hours is accepted | `cancellation.py` |
| Cancellation fee >24 hours before departure | 10% of fare | `cancellation.py` |
| Cancellation fee from 4 to 24 hours | 50% of fare | `cancellation.py` |
| Search response target | 5.0 seconds | `perf.py` and NFR-01 |
| PBKDF2 iteration count | 200,000 | `security.py` |
| Salt size | 16 random bytes (128 bits) | `security.py` |

Fare is calculated as the configured class fare multiplied by the number of travellers, rounded to two decimal places. Currency is displayed using the rupee symbol in the UI. The repository's demo data is illustrative and is not a live railway timetable or live fare feed.

## 10. Security and reliability

### 10.1 Password protection

- Passwords are not stored in plain text.
- `security.hash_password()` uses PBKDF2-HMAC-SHA256 with 200,000 iterations and a random 16-byte salt.
- Stored values have the form `salt_hex$digest_hex`.
- `verify_password()` uses `hmac.compare_digest` for digest comparison.
- Registration requires at least eight characters, including a letter and a digit.

### 10.2 Access control

- Roles are `passenger` and `admin`.
- Administrator operations call `require_admin()` (and the UI only displays the administration page to an admin).
- Passengers can access their own booking; administrators can access all bookings through the authorized service.
- A passenger attempting to view another passenger's PNR receives the same not-found behavior as an unknown PNR.

### 10.3 Database concurrency

Booking and cancellation use SQLite write transactions. They take the write lock before reading inventory (`BEGIN IMMEDIATE`, when no transaction is already active) and commit the related data changes together. The seat-allocation UNIQUE constraint provides a second database-level defense against duplicate seat assignment.

### 10.4 Backups

`backup.create_backup()` uses SQLite's online backup API, writes to a temporary file, validates it using `PRAGMA integrity_check`, and replaces the target atomically. `backup.restore_backup()` validates the source backup and restored temporary database before atomic replacement. See [SECURITY_AND_BACKUPS.md](SECURITY_AND_BACKUPS.md) for operational details.

### 10.5 Important deployment limitations

This is a course project and not a production railway booking service. In particular, the current code has in-memory sessions, demonstration credentials, a local SQLite file and no external identity provider, payment gateway, email/SMS integration, live train schedule integration, distributed locking or web API gateway. Do not deploy with demo credentials or treat the sample data as operational railway information.

## 11. Performance and measurable system properties

The repository defines measurable targets and invariants. A defined target is not the same as a measured result.

| Metric / invariant | Defined value | Measurement / verification status |
|---|---:|---|
| Train search response time (NFR-01) | ≤ 5.0 seconds | The `perf.py` helper can time a call and compare the limit; the recorded test execution log says TC-SEARCH-014 was not executed. No verified latency number is claimed here. |
| Session expiry | 1,800 seconds by default | Configured in code; automated session-related tests exist in the test tree, but record a fresh execution result when updating release evidence. |
| PBKDF2 work factor | 200,000 iterations | Fixed implementation constant in `security.py`; this is a configuration parameter, not an observed latency measurement. |
| PNR size | 10 decimal digits | Enforced by generator design and tests |
| Per-booking passenger cap | 6 | UI control, CLI constant and DB constraint |
| Historical automated suite | 286 passed, 0 failed; 99.70% coverage | Reported by the test execution log for its stated historical baseline and environment; not a claim about the current HEAD commit |
| CI coverage floor | 80% branch-aware coverage command threshold | Defined in GitHub Actions; current run status must be checked in Actions for each commit |

### 11.1 Reproducible search timing procedure

A latency measurement should specify the environment, dataset size, repetition count and statistic. The current helper measures a single function call. For a repeatable report, use a script or test that:

1. Seeds a known dataset and records the number of trains and stations.
2. Runs a fixed valid search query multiple times.
3. Records each elapsed time using `time.perf_counter()`.
4. Reports the median and maximum (and optionally p95) rather than presenting one run as a general result.
5. Records CPU, OS, Python version, commit SHA and whether the database is cold or warm.
6. Compares the measured result with the ≤5-second requirement.

Do not claim NFR-01 passes until that measurement has actually been run and recorded.

## 12. Testing and evidence

### 12.1 Test organization

The `tests/` directory contains focused test files for access control, authentication, availability, backup, booking, booking views, cancellation, CLI workflows, dates, demo data, integration, seat uniqueness, consistency, PNR, registration, search, performance, seats, security, storage and traveller validation.

The CI workflow runs on pushes and pull requests using Python 3.12 and performs:

```bash
python -m bandit -q -r src
python -m pip_audit -r requirements-dev.txt
python -m pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=80
```

### 12.2 Historical test report

`docs/testing/test-execution-log.md` records a run on **24 October 2026**, baseline commit `1ae7a7c`, Python 3.12.3 on Linux and pytest 9.1.1:

- 286 passed, 0 failed.
- 99.70% coverage was reported.
- The recorded concurrency scenarios include repeated attempts to book the last seat and mixed-size booking attempts.
- The log explicitly says search latency, usability, the UI cancellation confirmation step, and certain booking-view/administration/access-control cases were not executed at that baseline.

These numbers are historical evidence from that exact log, not current-HEAD test results. Re-run the complete suite on the current commit before a release or demonstration and update the execution log.

### 12.3 Current-source implementation versus historical test status

Some older planning/testing artefacts predate later Streamlit and backend work. In particular, the current source tree contains booking history, PNR detail viewing and train administration UI/service code, while the existing RTM/test-case files still show some of those cases as planned. Therefore:

- Treat the source presence as implementation evidence.
- Treat a test case marked PLANNED as not yet evidenced by that test artefact.
- Add/update automated tests and re-run them before changing a case to PASS.
- Add manual UI smoke-test evidence for browser workflows separately from backend unit-test evidence.

### 12.4 Existing testing documents

| Document | Purpose |
|---|---|
| [test-cases.md](testing/test-cases.md) | Test scenarios, preconditions, expected outcomes and historical status |
| [test-execution-log.md](testing/test-execution-log.md) | Execution environment, run result and unexecuted cases |
| [requirements-traceability-matrix.md](testing/requirements-traceability-matrix.md) | Requirement-to-test mapping |
| [software-test-plan.docx](testing/software-test-plan.docx) | Test planning document |
| [test-data.csv](testing/test-data.csv) | Test data |
| [railway-reservation-uml.puml](testing/railway-reservation-uml.puml) | UML source |
| [railway-reservation-uml.svg](testing/railway-reservation-uml.svg) | Rendered UML diagram |

## 13. Requirements and SDLC documentation index

| Artefact | Location | What it should contain / status |
|---|---|---|
| Software Requirements Specification | [SRS.docx](SRS.docx) | Formal scope and requirements; update when requirement decisions change |
| Software Architecture / Design | [SAD-doc.docx](SAD-doc.docx) | Intended architecture/design; compare against implementation and deviation log |
| Implemented requirements summary | [requirements.md](requirements.md) | Functional, non-functional and business rules |
| User stories | [user-stories.md](user-stories.md) | User goals and acceptance-oriented stories |
| Deviation log | [deviation-log.md](deviation-log.md) | Differences between submitted documents and actual build; resolve rows still marked Confirm/Open |
| Test plan and cases | `testing/` | Test approach and expected behavior |
| Requirements traceability | [requirements-traceability-matrix.md](testing/requirements-traceability-matrix.md) | Requirement-to-test links; refresh to match current implementation |
| Test execution evidence | [test-execution-log.md](testing/test-execution-log.md) | Dated results tied to a commit and environment |
| Security and backups | [SECURITY_AND_BACKUPS.md](SECURITY_AND_BACKUPS.md) | Password, session and database backup/restore details |
| Project/technical reference | This file | Current implementation and technical overview |

## 14. Known gaps, deviations and decisions to revisit

The following are visible from the inspected source and documentation. They should be reviewed rather than silently represented as complete:

1. **No REST API:** The SAD's REST-style endpoint examples are not implemented. The current contract is Python functions called in-process.
2. **Historical test artefacts need refresh:** The RTM and test-case statuses predate some current UI/backend features. Reconcile IDs, code paths and execution evidence.
3. **NFR-01 not measured:** A five-second limit exists, but the test log marks the timing test not executed.
4. **Usability not formally evaluated:** The Streamlit screen exists, but no recorded first-time-user study or task-completion evidence is supplied by the inspected files.
5. **UI smoke testing:** Backend tests are not substitutes for manually verifying register, login, search, booking, history, PNR, cancellation and admin screens in a browser.
6. **In-memory sessions:** A restart ends sessions; multiple independent app workers would not share them.
7. **Demo credentials:** Public credentials are included for local demonstration only.
8. **Deviation-log decisions:** Several rows remain marked Confirm/Open, including refund values, phone registration, waiting-list behavior and persistence status. Confirm decisions with the team and update the SRS/SAD/requirements consistently.
9. **No live railway integration:** Schedules, route availability, prices and sample trains come from the project's own SQLite data; they are not queried from a railway operator.

## 15. Documentation maintenance procedure

Update this file and the relevant detailed artefacts whenever a change affects requirements, architecture, UI, service signatures, database schema, validation rules, security, test cases or measured behavior.

For each change:

1. Record the requirement or issue being addressed.
2. Update the source and tests.
3. Update the relevant detailed document (SRS, SAD, requirements, test plan, cases, RTM, deviation log or security notes).
4. Update the relevant section in this technical reference.
5. Run the test suite and record the exact command, environment, commit SHA, pass/fail counts and coverage.
6. Record measurements with dataset and environment details; never invent or extrapolate results.
7. Submit the changes through a branch and pull request so reviewers can compare implementation and documentation.

### Documentation checklist for pull requests

- [ ] Does the documented behavior match the code?
- [ ] Are changed function signatures, validation rules and error cases described?
- [ ] Are schema/table or migration changes documented?
- [ ] Are frontend workflow changes described?
- [ ] Are tests added and mapped to requirement IDs?
- [ ] Are PASS/PLANNED/NOT EXECUTED statuses supported by recent execution evidence?
- [ ] Are performance/security numbers measured or clearly labelled as targets/configuration?
- [ ] Is the deviation log updated if implementation differs from the design?

---

**Document status:** Implementation reference for the current repository source tree inspected when this file was created. Revalidate against `main` after significant merges.  
**Maintainer:** Project team  

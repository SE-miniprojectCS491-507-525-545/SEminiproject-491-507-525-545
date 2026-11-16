# Requirements Traceability Matrix (RTM) — Current Implementation

**Scope:** This matrix maps the requirements in `docs/requirements.md` and the current source tree under `src/railway/`, `app.py` and `tests/`.

**Status convention:** "Automated evidence exists" means a corresponding pytest test is present in the repository. It does not claim that the latest commit has passed CI. See [test-execution-log.md](test-execution-log.md) for the historical run and GitHub Actions for the latest commit's result. Streamlit browser checks are tracked separately because the repository does not contain a browser automation suite.

## 1. Functional requirements

| Requirement ID | Requirement | Current implementation | Automated test evidence | Current verification status |
|---|---|---|---|---|
| FR-01 | Search trains by route and date | `search.py`; used by CLI and Streamlit `search_screen` | `test_search.py`, `test_search_results.py`, `test_search_availability_flow.py`; performance tests in `test_search_performance.py` | Implemented; automated service/CLI coverage exists; Streamlit browser smoke test pending |
| FR-02 | Check seat availability | `availability.py`; class-wise availability displayed by both frontends | `test_availability.py`, `test_search_availability_flow.py` | Implemented; automated service coverage exists; Streamlit browser smoke test pending |
| FR-03 | Validate train search input | `search.py`, `dates.py` | `test_search_validation.py`, `test_dates.py` | Implemented; automated coverage exists |
| FR-04 | Book ticket | `booking.py`, `storage.book_seats()`, `pnr.py`; CLI and Streamlit booking forms | `test_booking.py`, `test_pnr.py`, `test_seats.py`, `test_cli_bookings.py`, `test_integration.py` | Implemented; backend/CLI automated coverage exists; Streamlit browser smoke test pending |
| FR-05 | Validate traveller details | `traveller_validation.py`, DB constraints and booking input validation | `test_traveller_validation.py`, `test_booking.py`, `test_cli_bookings.py` | Implemented; automated coverage exists |
| FR-06 | Cancel ticket | `cancellation.cancel_booking()` and `storage.apply_cancellation()`; CLI and Streamlit cancellation flow | `test_cancellation.py`, `test_integration.py`, `test_booking.py`, `test_cli_bookings.py`, `test_nfr04_consistency.py` | Implemented; backend/CLI automated coverage exists; Streamlit browser smoke test pending |
| FR-07 | Calculate and show refund before cancellation | `calculate_refund()`, `preview_refund()`; CLI and Streamlit display refund before confirmation | `test_cancellation.py`, `test_cli_bookings.py` | Implemented; refund calculation, preview and CLI confirmation/decline are automated; Streamlit browser smoke test pending |
| FR-08 | Validate cancellation PNR | `cancellation.validate_cancellation()` and database cancellation path | `test_cancellation.py`, `test_integration.py`, `test_cli_bookings.py` | Implemented; automated coverage exists |
| FR-09 | Register passenger | `registration.py` and Streamlit/CLI registration workflows; SQLite persistence | `test_registration.py`, `test_integration.py`, `test_demo_data.py` | Implemented; service/storage integration coverage exists; Streamlit browser smoke test pending |
| FR-10 | Login and logout | `auth.py`, `SessionStore`, Streamlit and CLI login/logout | `test_auth.py`, `test_integration.py`, CLI tests | Implemented; service/CLI coverage exists, including expiry; Streamlit browser smoke test pending |
| FR-11 | View a booking by PNR | `booking_views.view_booking()`; CLI option and Streamlit PNR screen | `test_booking_views.py`, `test_cli_bookings.py` | Implemented; backend/CLI automated coverage exists; Streamlit browser smoke test pending |
| FR-12 | View own bookings | Storage passenger filter, CLI "My bookings", Streamlit `bookings_screen()` | `test_cli_bookings.py`; storage filtering in `test_storage.py` | Implemented; backend/CLI automated coverage exists; Streamlit browser smoke test pending |
| FR-13 | Admin adds train | Admin-protected CLI handler and Streamlit administration tab; `storage.add_train()` | `test_cli_admin_trains.py`, `test_storage.py` | Implemented; CLI/backend automated coverage exists; Streamlit browser smoke test pending |
| FR-14 | Admin updates/removes train | Admin-protected CLI handlers and Streamlit administration tabs; removal deactivates train and protects confirmed bookings | `test_cli_admin_trains.py`, `test_storage.py` | Implemented; CLI/backend automated coverage exists; Streamlit browser smoke test pending |
| FR-15 | Admin views all bookings | `booking_views.list_all_bookings()` service with admin authorization | `test_booking_views.py` | Backend service implemented and tested. No admin-wide booking list screen is present in current Streamlit UI or CLI menu; user-facing workflow is not implemented |

## 2. Business rules

| Requirement ID | Rule | Current implementation | Automated test evidence | Current verification status |
|---|---|---|---|---|
| BR-01 | Maximum 6 passengers per booking | Validation in booking/CLI, Streamlit input cap, database CHECK constraint | `test_booking.py`, `test_cli_bookings.py`, `test_storage.py` | Implemented; automated coverage exists |
| BR-02 | Cancellation deadline and refund fee slabs | Four-hour cancellation cutoff; 10% fee when more than 24 hours remain; 50% fee from 4–24 hours | `test_cancellation.py`, `test_cli_bookings.py`, `test_integration.py` | Implemented; automated boundary and refund tests exist |

## 3. Non-functional requirements

| Requirement ID | Requirement | Current implementation | Automated test evidence | Current verification status |
|---|---|---|---|---|
| NFR-01 | Search response time ≤ 5 seconds | `perf.py` provides timing and threshold helpers; tests seed 20,000 trains over 200 stations and exercise high-result routes | `test_search_performance.py` | Automated performance tests exist and assert the 5-second target. The historical execution log does not record a performance run or actual latency values; use current CI/run output as evidence |
| NFR-02 | First-time user can search without external help | Streamlit search uses source/destination selectors, date input and visible errors/hints; CLI has search hints | `test_cli_search_usability.py`, `test_search_help.py` test CLI guidance, not a formal user study | Partially verified: code and CLI guidance tests exist; no recorded first-time-user usability study or Streamlit user test |
| NFR-03 | Never assign the same seat twice | SQLite `BEGIN IMMEDIATE` booking transaction plus UNIQUE constraint on train/date/class/seat number | `test_nfr03_no_duplicate_seats.py`, `test_booking.py`, `test_seats.py` | Implemented; automated concurrency tests exist |
| NFR-04 | Cancelled seats become available immediately and counts stay consistent | Atomic cancellation updates status, availability and seat allocations; consistency checker | `test_nfr04_consistency.py`, `test_booking.py`, `test_integration.py` | Implemented; automated consistency, concurrent operation and next-connection visibility tests exist |
| NFR-05 | Data persistence | SQLite file database and schema initialization in `storage.py` | `test_storage.py`, `test_integration.py` | Implemented; automated storage/persistence tests exist |

## 4. Security requirements

| Requirement ID | Requirement | Current implementation | Automated test evidence | Current verification status |
|---|---|---|---|---|
| SR-01 | Passwords protected using salted hashing | PBKDF2-HMAC-SHA256, 16-byte random salt, 200,000 iterations and constant-time digest comparison | `test_security.py`, `test_registration.py` | Implemented; automated coverage exists |
| SR-02 | Role-based and booking-ownership access control | Passenger/admin roles, `require_admin()`, `can_access_booking()`, protected booking views and admin CLI/UI gating | `test_access.py`, `test_booking_views.py`, `test_cli_admin_trains.py`, `test_cli_bookings.py` | Implemented; backend/CLI coverage exists; Streamlit role-gating browser smoke test pending |

## 5. Additional implemented features (not standalone SRS IDs)

| Feature | Implementation | Automated test evidence | Current verification status |
|---|---|---|---|
| SQLite backup | `backup.create_backup()` uses SQLite online backup API, temporary output and integrity validation | `test_backup.py` | Implemented and automated tests exist |
| SQLite restore | `backup.restore_backup()` validates source and restored DB then atomically replaces destination | `test_backup.py` | Implemented and automated tests exist |
| Database consistency diagnostics | `consistency.find_inconsistencies()` checks free counts, held seat count and seat-number bounds | `test_nfr04_consistency.py` | Implemented and automated tests exist |
| Demo passenger/admin accounts | `demo_data.seed_demo_data()` creates sample trains and separate passenger/admin accounts | `test_demo_data.py`, `test_cli_main.py` | Implemented and automated tests exist; browser action still needs manual UI smoke test |

## 6. UI verification matrix

The existence of Streamlit UI code does not establish that the browser workflow has been manually executed. There is no dedicated Streamlit browser automation suite in the current test tree.

| UI workflow | Current Streamlit screen | Backend/CLI test evidence | Browser validation |
|---|---|---|---|
| Registration | Register | Registration/service tests | Pending manual smoke test |
| Login/logout and session expiry | Log in; sidebar logout | Authentication and CLI tests | Pending manual smoke test |
| Train search | Search trains | Search service and CLI tests | Pending manual smoke test |
| Seat availability | Seat availability | Availability tests | Pending manual smoke test |
| Booking | Book ticket | Booking service and CLI tests | Pending manual smoke test |
| Passenger booking history | My bookings | CLI history and storage tests | Pending manual smoke test |
| PNR lookup | Find booking by PNR | Booking view and CLI tests | Pending manual smoke test |
| Refund preview/cancellation | Cancel booking | Cancellation and CLI tests | Pending manual smoke test |
| Train administration | Add, Update, Remove tabs | CLI admin and storage tests | Pending manual smoke test |
| Admin-wide booking list | No current screen | Backend service test only | Not available in current UI |

## 7. Test execution evidence

The repository's [test execution log](test-execution-log.md) records a historical run dated 24 October 2026, against baseline commit `1ae7a7c`, with 286 passed, 0 failed and 99.70% coverage. That log explicitly noted some features as not built at that earlier baseline. This RTM updates implementation mapping against the current source and test files, but it does not rewrite that historical record or claim the current HEAD has the same results.

The CI workflow in `.github/workflows/ci.yml` runs Bandit, pip-audit and pytest with branch-aware coverage and an 80% minimum on pushes and pull requests. Check the relevant GitHub Actions run for the current commit before recording a fresh PASS result.

## 8. Traceability maintenance rules

- When a requirement changes, update its requirement text and ID in the requirements/SRS documents as agreed by the team.
- Every implemented requirement should map to one or more tests that verify its acceptance criteria.
- Keep unit/service, CLI integration and Streamlit UI evidence distinguishable.
- Mark a requirement fully verified only when implementation and the appropriate test evidence both exist.
- For any requirement only partially implemented, state which layer is missing instead of marking it complete.
- Do not backdate test results or reuse a historical coverage number as a current result.

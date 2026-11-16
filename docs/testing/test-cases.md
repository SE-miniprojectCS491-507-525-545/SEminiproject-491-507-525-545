# Test Cases — Railway Reservation System

**Scope:** This catalogue is aligned with the implementation currently present in `main` and the automated tests under `tests/`. It includes backend/service and CLI scenarios, plus separate manual Streamlit checks.

**Important status note:** The status in this file describes whether a corresponding test exists in the repository, not whether it passed in the latest CI run. Use [test-execution-log.md](test-execution-log.md) and GitHub Actions for dated execution results. Do not turn a test into PASS merely because the related function exists.

## 1. Status definitions

| Status | Meaning |
|---|---|
| **AUTOMATED — COVERED** | A corresponding pytest test is present in the repository. Check CI or a dated execution log for the result on a particular commit. |
| **AUTOMATED — BACKEND/CLI ONLY** | Logic is tested through Python services or the CLI; this is not evidence that the Streamlit browser workflow was tested. |
| **MANUAL UI — PENDING** | The Streamlit screen exists, but no automated browser/UI test or recorded manual execution is present in the inspected repository. |
| **PARTIAL** | Some layers or scenarios are covered, but the full requirement is not verified. |
| **NOT IMPLEMENTED** | The described behavior is not present in the current source. |

**Testing layers:** Service tests exercise individual Python functions. CLI tests exercise scripted command-line interactions. Neither category is a browser-based end-to-end test of Streamlit.

## 2. Train search and availability

| Test Case ID | Requirement | Scenario | Test data / precondition | Expected result | Automated evidence | Status |
|---|---|---|---|---|---|---|
| TC-SEARCH-001 | FR-01 | Search a valid route | Known source, destination and a future travel date | Matching trains that operate on that weekday are returned | `tests/test_search.py`, `tests/test_search_results.py` | AUTOMATED — COVERED |
| TC-SEARCH-002 | FR-01 | Normalize case and surrounding spaces | Source and destination supplied with mixed case and spaces | Search succeeds after normalization | `tests/test_search.py` | AUTOMATED — COVERED |
| TC-SEARCH-003 | FR-01 | Search a route with no matching train | Known stations with no matching direct service | Empty result is returned | `tests/test_search.py`, `tests/test_search_results.py` | AUTOMATED — COVERED |
| TC-SEARCH-004 | FR-01 | Respect train operating weekdays | Search the same route on a day the train runs and a day it does not | Train appears only on a permitted operating day | `tests/test_search.py` | AUTOMATED — COVERED |
| TC-SEARCH-005 | FR-03 | Reject missing or invalid search fields | Empty source, empty destination, missing/malformed date | A clear validation error is raised | `tests/test_search_validation.py`, `tests/test_dates.py` | AUTOMATED — COVERED |
| TC-SEARCH-006 | FR-03 | Reject unknown or identical stations | Unknown source/destination; same source and destination | Search is rejected with an explanatory error | `tests/test_search_validation.py` | AUTOMATED — COVERED |
| TC-SEARCH-007 | FR-03 | Reject past travel dates | Travel date earlier than the reference date | Search is rejected; today is accepted | `tests/test_search_validation.py`, `tests/test_dates.py` | AUTOMATED — COVERED |
| TC-SEARCH-008 | FR-01 / NFR-01 | Search a large train dataset | 20,000 trains across 200 stations | Search completes within the 5-second threshold | `tests/test_search_performance.py::test_search_over_20000_trains_is_within_5_seconds` | AUTOMATED — COVERED |
| TC-SEARCH-009 | FR-01 / NFR-01 | Search a busy route and retrieve class availability | Route has 300 matching trains; two classes per train | Search and availability lookup for all results complete within 5 seconds | `tests/test_search_performance.py::test_search_with_hundreds_of_results_incl_seat_lookup_is_within_5_seconds` | AUTOMATED — COVERED |
| TC-SEARCH-010 | FR-01 / NFR-01 | Search a route with no matches under the performance threshold | Large seeded train dataset; route returns no matches | Empty result is returned within 5 seconds | `tests/test_search_performance.py::test_search_with_no_matches_is_within_5_seconds` | AUTOMATED — COVERED |
| TC-AVAIL-001 | FR-02 | Show availability for every class | Valid train and date with multiple seat classes | Each class displays total seats, free seats, fare and availability status | `tests/test_availability.py`, `tests/test_search_availability_flow.py` | AUTOMATED — COVERED |
| TC-AVAIL-002 | FR-02 | Treat an uninitialized availability row as full capacity | Valid train/date/class with no availability row yet | All configured seats are initially considered free | `tests/test_availability.py` | AUTOMATED — COVERED |
| TC-AVAIL-003 | FR-02 | Report a sold-out class | Selected class has zero free seats | Status is `SOLD OUT`; no waiting-list allocation is created | `tests/test_availability.py`, `tests/test_booking.py` | AUTOMATED — COVERED |
| TC-AVAIL-004 | FR-02 / FR-03 | Reject invalid availability requests | Unknown train/class, past date or non-operating weekday | Availability lookup raises a clear validation error | `tests/test_availability.py` | AUTOMATED — COVERED |

## 3. Registration, authentication and access control

| Test Case ID | Requirement | Scenario | Test data / precondition | Expected result | Automated evidence | Status |
|---|---|---|---|---|---|---|
| TC-REG-001 | FR-09 | Register a valid passenger | Name, unique email and valid password | Passenger account is created and email is normalized | `tests/test_registration.py`, `tests/test_integration.py` | AUTOMATED — COVERED |
| TC-REG-002 | FR-09 | Reject invalid registration fields | Missing name/email/password, malformed email, short or weak password | Registration is rejected; no invalid account is created | `tests/test_registration.py` | AUTOMATED — COVERED |
| TC-REG-003 | FR-09 | Reject duplicate email | Email already exists, including case/space variations | Duplicate account is refused | `tests/test_registration.py` | AUTOMATED — COVERED |
| TC-LOGIN-001 | FR-10 | Log in with valid credentials | Registered passenger | A new session token is returned and associated with the passenger | `tests/test_auth.py`, `tests/test_integration.py` | AUTOMATED — COVERED |
| TC-LOGIN-002 | FR-10 | Reject wrong password and unknown email consistently | Incorrect password; unregistered email | Both cases produce the same generic login error | `tests/test_auth.py` | AUTOMATED — COVERED |
| TC-LOGIN-003 | FR-10 | Logout invalidates a session | Valid session token | Token is removed; subsequent access is rejected | `tests/test_auth.py` | AUTOMATED — COVERED |
| TC-LOGIN-004 | FR-10 | Expire an inactive session | Session TTL configured to 10 seconds; simulated monotonic clock | Session expires at the configured boundary and is removed | `tests/test_auth.py::test_session_expires_after_configured_timeout` | AUTOMATED — COVERED |
| TC-LOGIN-005 | FR-10 | Reject invalid session timeout configuration | TTL is zero or non-integer | Authentication raises a configuration error | `tests/test_auth.py` | AUTOMATED — COVERED |
| TC-SEC-001 | SR-01 | Store passwords as salted hashes | Register the same password for separate accounts | Plain-text password is not stored; independent salts produce different stored hashes | `tests/test_security.py`, `tests/test_registration.py` | AUTOMATED — COVERED |
| TC-SEC-002 | SR-01 | Verify correct and incorrect passwords | Stored password hash | Correct password verifies; wrong or malformed values fail safely | `tests/test_security.py` | AUTOMATED — COVERED |
| TC-SEC-003 | SR-02 | Enforce administrator role | Passenger, admin and unauthenticated user attempt admin-only helper | Only admin is accepted by `require_admin` | `tests/test_access.py`, `tests/test_cli_admin_trains.py` | AUTOMATED — COVERED |
| TC-SEC-004 | SR-02 | Restrict booking access to its owner | Passenger tries own and another passenger's booking; admin checks another booking | Owner and admin are allowed; unrelated passenger is denied | `tests/test_access.py`, `tests/test_booking_views.py`, `tests/test_cli_bookings.py` | AUTOMATED — COVERED |

## 4. Booking, PNR and passenger validation

| Test Case ID | Requirement | Scenario | Test data / precondition | Expected result | Automated evidence | Status |
|---|---|---|---|---|---|---|
| TC-BOOK-001 | FR-04 | Book a valid ticket | Registered passenger, operating train, future date, valid class and travellers | Confirmed Ticket with PNR, allocated seats and total fare is returned | `tests/test_booking.py` | AUTOMATED — COVERED |
| TC-BOOK-002 | FR-04 | Persist booking and traveller details | Successful booking with multiple travellers | Booking, travellers and seat allocations are saved and can be read back | `tests/test_booking.py`, `tests/test_storage.py` | AUTOMATED — COVERED |
| TC-BOOK-003 | FR-04 | Reduce availability after booking | Book two seats in a class | Free-seat count decreases by two | `tests/test_booking.py` | AUTOMATED — COVERED |
| TC-BOOK-004 | FR-05 | Reject invalid traveller details | Empty/invalid name, age outside 1–120, invalid gender | Booking is rejected before any booking or inventory change | `tests/test_booking.py`, `tests/test_traveller_validation.py` | AUTOMATED — COVERED |
| TC-BOOK-005 | BR-01 | Enforce maximum of six travellers | Submit six and then seven travellers | Six are accepted when capacity permits; seven are rejected | `tests/test_booking.py`, `tests/test_cli_bookings.py`, database CHECK constraint | AUTOMATED — COVERED |
| TC-BOOK-006 | FR-04 | Reject booking without a registered account | Missing, blank or unknown passenger email | Booking is refused and no booking is stored | `tests/test_booking.py` | AUTOMATED — COVERED |
| TC-BOOK-007 | FR-04 | Reject invalid train, date, operating day or class | Unknown train, past date, non-running day or unavailable class | Booking is rejected without changing inventory | `tests/test_booking.py` | AUTOMATED — COVERED |
| TC-BOOK-008 | FR-04 | Reject insufficient seats | Requested traveller count exceeds remaining inventory | Booking fails and existing booking/availability state stays unchanged | `tests/test_booking.py` | AUTOMATED — COVERED |
| TC-BOOK-009 | FR-04 | Allocate unique PNRs and valid seat numbers | Multiple successful bookings | PNRs are unique 10-digit numbers; seat numbers are distinct and within class capacity | `tests/test_booking.py`, `tests/test_pnr.py`, `tests/test_seats.py` | AUTOMATED — COVERED |
| TC-BOOK-010 | FR-04 / NFR-03 | Roll back a booking that fails part-way | Simulated database failure during seat allocation | No partial booking, traveller, availability or seat-allocation changes remain | `tests/test_booking.py` | AUTOMATED — COVERED |
| TC-BOOK-011 | NFR-03 | Concurrent users compete for limited seats | 12 users compete for 5 seats; other multi-size and last-seat races | Only capacity-fitting bookings succeed; no duplicate seat number is assigned | `tests/test_nfr03_no_duplicate_seats.py`, `tests/test_booking.py` | AUTOMATED — COVERED |

## 5. Booking history and PNR viewing

| Test Case ID | Requirement | Scenario | Test data / precondition | Expected result | Automated evidence | Status |
|---|---|---|---|---|---|---|
| TC-HIST-001 | FR-12 | Passenger views own booking history | Passenger has multiple bookings; another passenger also has bookings | Only the logged-in passenger's bookings are displayed | `tests/test_cli_bookings.py::test_my_bookings_lists_only_my_own`; Streamlit `bookings_screen` uses passenger email filter | AUTOMATED — BACKEND/CLI ONLY |
| TC-HIST-002 | FR-12 | Passenger has no bookings | Logged-in passenger has no records | Clear empty-state message is displayed | `tests/test_cli_bookings.py::test_my_bookings_when_empty`; Streamlit `bookings_screen` has empty state | AUTOMATED — BACKEND/CLI ONLY |
| TC-PNR-001 | FR-11 | View an existing booking by PNR | Existing booking owned by the passenger | Train name, status, date, class, travellers, seats and fare are returned/formatted | `tests/test_booking_views.py`, `tests/test_cli_bookings.py` | AUTOMATED — BACKEND/CLI ONLY |
| TC-PNR-002 | FR-11 | Reject blank or unknown PNR | Blank, whitespace or unknown PNR | A clear not-found or required-field error is produced | `tests/test_booking_views.py`, `tests/test_cli_bookings.py` | AUTOMATED — COVERED |
| TC-PNR-003 | SR-02 | Prevent a passenger from viewing another person's PNR | PNR belongs to a different passenger | Booking details are not disclosed; response behaves like not found | `tests/test_booking_views.py`, `tests/test_cli_bookings.py` | AUTOMATED — COVERED |
| TC-PNR-004 | SR-02 | Allow administrator to view any booking | Admin requests a passenger's PNR | Booking details can be returned to the admin | `tests/test_booking_views.py` | AUTOMATED — COVERED |

## 6. Cancellation and refund

| Test Case ID | Requirement | Scenario | Test data / precondition | Expected result | Automated evidence | Status |
|---|---|---|---|---|---|---|
| TC-CAN-001 | FR-06 | Cancel an active booking | Valid confirmed PNR and time at least four hours before departure | Booking status changes to CANCELLED; seats are released | `tests/test_cancellation.py`, `tests/test_integration.py` | AUTOMATED — COVERED |
| TC-CAN-002 | FR-08 | Reject blank or unknown PNR | Empty or unknown PNR | Cancellation is rejected with an explanatory error | `tests/test_cancellation.py`, `tests/test_integration.py` | AUTOMATED — COVERED |
| TC-CAN-003 | FR-08 | Reject repeated cancellation | PNR already has CANCELLED status | Second cancellation is rejected; seat count does not increase again | `tests/test_cancellation.py`, `tests/test_integration.py`, `tests/test_cli_bookings.py` | AUTOMATED — COVERED |
| TC-CAN-004 | BR-02 | Enforce the four-hour cancellation cutoff | Exactly four hours, three hours 59 minutes, and after departure | Exactly four hours is allowed; closer than four hours and post-departure cancellation are refused | `tests/test_cancellation.py`, `tests/test_cli_bookings.py` | AUTOMATED — COVERED |
| TC-REF-001 | FR-07 / BR-02 | Calculate refund more than 24 hours before departure | Fare and departure time with more than 24 hours remaining | 10% fee is deducted; refund is 90% of fare | `tests/test_cancellation.py`, `tests/test_cli_bookings.py` | AUTOMATED — COVERED |
| TC-REF-002 | FR-07 / BR-02 | Calculate refund from 4 to 24 hours before departure | Fare and departure time within this window, including exact 24 and 4-hour boundaries | 50% fee is deducted; refund is 50% of fare | `tests/test_cancellation.py`, `tests/test_cli_bookings.py` | AUTOMATED — COVERED |
| TC-REF-003 | FR-07 | Preview refund without cancelling | Eligible confirmed booking | Refund is returned/displayed while booking and seat state remain unchanged | `tests/test_cancellation.py`, `tests/test_cli_bookings.py` | AUTOMATED — COVERED |
| TC-REF-004 | FR-07 | Passenger declines cancellation | Passenger chooses No/keep booking after refund preview | Booking stays confirmed and seats remain allocated | `tests/test_cli_bookings.py::test_cancel_declined_changes_nothing` | AUTOMATED — BACKEND/CLI ONLY |
| TC-REF-005 | FR-07 | Confirm cancellation after preview in Streamlit | Logged-in owner/admin with eligible booking | UI displays refund estimate; confirmation changes booking status and releases seats | Streamlit `cancel_screen` | MANUAL UI — PENDING |

## 7. Administration

| Test Case ID | Requirement | Scenario | Test data / precondition | Expected result | Automated evidence | Status |
|---|---|---|---|---|---|---|
| TC-ADM-001 | FR-13 | Admin adds a valid train | Admin account and unique train number with valid schedule/class details | Train and initial class are stored and become searchable | `tests/test_cli_admin_trains.py`; Streamlit `admin_screen` add tab | AUTOMATED — BACKEND/CLI ONLY |
| TC-ADM-002 | FR-13 | Reject duplicate train number or missing required fields | Existing train number or blank required value | Train is not added and a clear error is returned | `tests/test_cli_admin_trains.py` | AUTOMATED — COVERED |
| TC-ADM-003 | FR-14 | Admin updates train details | Existing train and valid replacement values | Updated train details are persisted | `tests/test_cli_admin_trains.py`; Streamlit `admin_screen` update tab | AUTOMATED — BACKEND/CLI ONLY |
| TC-ADM-004 | FR-14 | Admin deactivates a train without confirmed bookings | Existing train with no confirmed bookings | Train becomes inactive and is omitted from active train listings | `tests/test_cli_admin_trains.py`, `tests/test_storage.py` | AUTOMATED — COVERED |
| TC-ADM-005 | FR-14 | Prevent removal of a train with confirmed bookings | Train has at least one confirmed booking | Removal is refused and train remains active | `tests/test_cli_admin_trains.py` | AUTOMATED — COVERED |
| TC-ADM-006 | FR-13 / FR-14 / SR-02 | Prevent passenger or logged-out user from changing trains | Passenger or unauthenticated user attempts add/update/remove | Access is denied and train data remains unchanged | `tests/test_cli_admin_trains.py`, `tests/test_access.py` | AUTOMATED — COVERED |
| TC-ADM-007 | FR-15 | Admin retrieves all bookings through the backend service | Multiple passengers have bookings; admin calls `list_all_bookings` | All bookings are returned in PNR order; an empty database returns an empty list | `tests/test_booking_views.py` | AUTOMATED — BACKEND ONLY |
| TC-ADM-008 | FR-15 | Passenger is prevented from retrieving the admin-wide booking list | Passenger or unauthenticated user calls `list_all_bookings` | Access is rejected | `tests/test_booking_views.py` | AUTOMATED — COVERED |

**FR-15 interface note:** The backend function `booking_views.list_all_bookings()` exists and is tested, but the inspected Streamlit admin page only provides Add, Update and Remove train tabs, and the CLI menu does not expose an admin-wide bookings option. The requirement is therefore covered at service level, not as an end-user admin screen.

## 8. Persistence, consistency, backup and reliability

| Test Case ID | Requirement | Scenario | Test data / precondition | Expected result | Automated evidence | Status |
|---|---|---|---|---|---|---|
| TC-DATA-001 | NFR-05 | Data survives closing and reopening the database | Save records, close connection and open the same database file | Persisted trains, passengers, bookings and related records remain available | `tests/test_storage.py`, `tests/test_integration.py` | AUTOMATED — COVERED |
| TC-DATA-002 | NFR-04 | A cancelled seat is immediately visible to another open connection | Two SQLite connections; one performs cancellation | Other connection immediately sees the restored free count and can book the released seats | `tests/test_nfr04_consistency.py::test_another_open_connection_sees_the_cancelled_seat_straight_away` | AUTOMATED — COVERED |
| TC-DATA-003 | NFR-04 | Verify consistency over a long booking/cancellation history | 200 deterministic randomized booking/cancellation steps | Consistency checker reports no mismatch after each step | `tests/test_nfr04_consistency.py::test_counts_stay_consistent_through_two_hundred_random_bookings_and_cancellations` | AUTOMATED — COVERED |
| TC-DATA-004 | NFR-04 | Detect damaged availability/seat-allocation records | Deliberately alter free counts, delete availability/seat records or set an out-of-range seat number | Consistency checker reports the mismatch | `tests/test_nfr04_consistency.py` | AUTOMATED — COVERED |
| TC-DATA-005 | NFR-04 / NFR-03 | Handle concurrent cancellations and concurrent booking/cancellation | Separate database connections and multiple threads | No lost free seats or duplicated allocated seat numbers; counts remain within capacity | `tests/test_nfr04_consistency.py` | AUTOMATED — COVERED |
| TC-DATA-006 | NFR-03 | Enforce seat uniqueness in the database | Attempt to allocate the same train/date/class seat twice | UNIQUE constraint rejects the duplicate allocation | `tests/test_storage.py`, `tests/test_seats.py`, `tests/test_nfr03_no_duplicate_seats.py` | AUTOMATED — COVERED |
| TC-BACKUP-001 | Operational feature | Create a valid SQLite backup | Existing source database and different destination | Backup file is created and contains the source data | `tests/test_backup.py` | AUTOMATED — COVERED |
| TC-BACKUP-002 | Operational feature | Restore a valid SQLite backup | Valid backup and separate destination database | Destination is replaced with the validated backup content | `tests/test_backup.py` | AUTOMATED — COVERED |
| TC-BACKUP-003 | Operational feature | Reject invalid backup and unsafe same-file operations | Corrupt backup or same source/destination path | Restore/backup is refused; existing destination remains unchanged | `tests/test_backup.py` | AUTOMATED — COVERED |

## 9. Streamlit browser smoke tests

These cases are intentionally separate from pytest service/CLI cases. The source contains the Streamlit screens, but the inspected repository does not contain a browser automation suite or a dated manual UI execution record. Execute these in a browser and record the tester, date, commit, browser/OS and observed result before marking them PASS.

| Test Case ID | Screen / feature | Steps | Expected result | Status |
|---|---|---|---|---|
| TC-UI-001 | Application launch and connection lifecycle | Start with `PYTHONPATH=src streamlit run app.py`; navigate and trigger multiple reruns | App loads without SQLite cross-thread errors; connection is usable on each rerun | MANUAL UI — PENDING |
| TC-UI-002 | Demo data | Use Load demo data on an empty DB, then click it again | Sample trains and separate passenger/admin demo accounts are available; second load does not duplicate train data | MANUAL UI — PENDING |
| TC-UI-003 | Registration and login | Register a valid passenger, attempt invalid registration, log in, log out | Validation messages appear; valid account can log in; logout returns to unauthenticated navigation | MANUAL UI — PENDING |
| TC-UI-004 | Train search | Search a valid route/date, then a route with no result | Matching trains and class availability appear; no-match state is clear | MANUAL UI — PENDING |
| TC-UI-005 | Seat availability | Select a train and date with available and sold-out classes | Class, total seats, free seats, fare and status are displayed correctly | MANUAL UI — PENDING |
| TC-UI-006 | Booking | Book one passenger and then a multi-passenger booking; inspect confirmation | Booking confirmation shows PNR, train, date, class, allocated seats and total fare | MANUAL UI — PENDING |
| TC-UI-007 | My bookings | Log in as a passenger with bookings and as a new passenger | Only the signed-in passenger's bookings appear; empty state is shown when none exist | MANUAL UI — PENDING |
| TC-UI-008 | PNR lookup | Open own PNR and then another passenger's/unknown PNR | Own booking details appear; unrelated/unknown booking is not disclosed | MANUAL UI — PENDING |
| TC-UI-009 | Refund preview and cancellation | Preview refund, leave without confirmation, then preview and confirm an eligible cancellation | Preview alone changes nothing; confirmed cancellation displays result and returns seats to availability | MANUAL UI — PENDING |
| TC-UI-010 | Administrator train management | Log in as demo admin; add, edit and deactivate a train; repeat as passenger | Admin controls work and persist changes; passenger does not see or access admin controls | MANUAL UI — PENDING |

## 10. Source-to-test file index

| Test file | Main coverage |
|---|---|
| `tests/test_access.py` | Roles, admin authorization and booking ownership |
| `tests/test_auth.py` | Login/logout, generic authentication failures and expiry |
| `tests/test_availability.py` | Availability, sold-out state and date/train/class validation |
| `tests/test_backup.py` | SQLite backup and restore validation |
| `tests/test_booking.py` | Booking, traveller validation, PNR, inventory and rollback |
| `tests/test_booking_views.py` | PNR details, admin-wide booking list and ownership |
| `tests/test_cancellation.py` | Cancellation validation, deadline and refund calculations |
| `tests/test_cli_admin_trains.py` | CLI add/update/remove train and role restrictions |
| `tests/test_cli_bookings.py` | CLI booking, history, PNR, cancellation and refund confirmation |
| `tests/test_integration.py` | Cross-module registration/login and database cancellation |
| `tests/test_nfr03_no_duplicate_seats.py` | Concurrent seat allocation |
| `tests/test_nfr04_consistency.py` | Consistency checker, long histories and concurrent booking/cancellation |
| `tests/test_pnr.py` | PNR length, range, uniqueness retry and retry exhaustion |
| `tests/test_registration.py` | Registration validation and password storage |
| `tests/test_search.py`, `tests/test_search_results.py` | Search and result matching |
| `tests/test_search_performance.py` | 20,000-train and high-result-count performance thresholds |
| `tests/test_search_validation.py`, `tests/test_dates.py` | Search/date input validation |
| `tests/test_seats.py` | Seat-number allocation |
| `tests/test_security.py` | Salted password hashing and verification |
| `tests/test_storage.py` | SQLite schema, persistence and storage operations |
| `tests/test_traveller_validation.py` | Traveller-field validation |

## 11. Execution and maintenance rules

1. Run the full suite after changes: `PYTHONPATH=src python -m pytest`.
2. Match test results to a commit SHA. A result from an older commit must remain labelled historical.
3. Use GitHub Actions as the authoritative CI result for the pushed/pull-request commit.
4. For every new or changed requirement, update the requirement ID, test case and traceability matrix together.
5. For UI changes, add browser automation where practical; otherwise record manual smoke-test evidence separately.
6. Update the status only when evidence exists. **Code present is not the same as a test passing; a backend test is not the same as a UI test passing.**

# Test Cases — Railway Reservation System

**Baseline date:** 22 October 2026  
**Priority:** H = High; M = Medium.  
**Status rule:** PASS means executed successfully on the current implementation. PLANNED means the feature is not yet implemented. NOT EXECUTED means designed but not yet run.

| Test Case ID | Requirement | Scenario | Test data / precondition | Expected result | Priority | Status |
|---|---|---|---|---|---|---|
| TC-SEARCH-001 | FR-01 | Search a valid route | Bengaluru → Chennai; 06-Oct-2026 | Matching train is returned | H | PASS |
| TC-SEARCH-002 | FR-01 | Normalize case and surrounding spaces | `  bengaluru ` → `CHENNAI` | Input is normalized and matching train is returned | M | PASS |
| TC-SEARCH-003 | FR-01 | Search a route with no matching train | Chennai → Mysuru | Empty result is returned | M | PASS |
| TC-SEARCH-004 | FR-01 | Exclude a train not running on the selected weekday | Bengaluru → Mysuru; 06-Oct-2026 (Tuesday) | Shatabdi is excluded because it does not run Tuesday | H | PASS |
| TC-SEARCH-005 | FR-01 | Include a train running on the selected weekday | Bengaluru → Mysuru; 07-Oct-2026 (Wednesday) | Shatabdi is returned | H | PASS |
| TC-SEARCH-006 | FR-03 | Empty source | Source = empty string | Clear source-required error is raised | H | PASS |
| TC-SEARCH-007 | FR-03 | Empty destination | Destination = empty string | Clear destination-required error is raised | H | PASS |
| TC-SEARCH-008 | FR-03 | Missing travel date | Travel date = `None` | Clear travel-date-required error is raised | H | PASS |
| TC-SEARCH-009 | FR-03 | Unknown source station | Atlantis → Chennai | Unknown-station error is raised | H | PASS |
| TC-SEARCH-010 | FR-03 | Unknown destination station | Bengaluru → Atlantis | Unknown-station error is raised | H | PASS |
| TC-SEARCH-011 | FR-03 | Same source and destination | Chennai → Chennai | Same-station error is raised | H | PASS |
| TC-SEARCH-012 | FR-03 | Past travel date | 01-Oct-2026; test reference date = 05-Oct-2026 | Past-date error is raised | H | PASS |
| TC-SEARCH-013 | FR-03 | Allow the reference date itself | 05-Oct-2026; test reference date = 05-Oct-2026 | Date is accepted | M | PASS |
| TC-SEARCH-014 | NFR-01 | Measure search response time | Valid search on an integrated build | Results returned within 5 seconds under normal conditions | H | NOT EXECUTED |
| TC-AVAIL-001 | FR-02 | Show seat counts by class | Valid train/date; availability module implemented | Available seats are shown per class | H | PASS |
| TC-AVAIL-002 | FR-02 | Handle a full class | Selected class has zero seats | Class is reported as sold out (0 free seats). There is no waiting list (deviation log #9) | H | PASS |
| TC-BOOK-001 | FR-04 | Book when seats are available | Valid passenger details and available class | Booking succeeds and a unique PNR is returned (confirmation text; no screen yet) | H | PASS |
| TC-BOOK-002 | FR-04 | Update availability after booking | Book two seats | Available count decreases by two | H | PASS |
| TC-BOOK-003 | FR-05 | Reject empty passenger name | Name = empty string | Booking is rejected with a field-specific error | M | PASS |
| TC-BOOK-004 | FR-05 | Reject invalid passenger age | Age = 0 or 121 | Booking is rejected with an age validation error | M | PASS |
| TC-BOOK-005 | BR-01 | Reject more than six passengers | Seven passengers in one booking | Booking is rejected; maximum remains six | H | PASS |
| TC-BOOK-006 | NFR-03 | Two users attempt to book the final seat | Two simultaneous requests; one seat remaining | Exactly one booking succeeds; the other receives no-seat response | H | PASS |
| TC-BOOK-007 | FR-04 | PNR is a unique 10-digit number | Several bookings in a row; a PNR that is already used | Every PNR has 10 digits, does not start with 0, and is different from all others | H | PASS |
| TC-BOOK-008 | FR-04 | Seats are allocated and reused | Book two seats, then book again; cancel and book again | Lowest free seat numbers are given; cancelled seats are given out again; no seat is held twice | H | PASS |
| TC-CAN-001 | FR-06 | Cancel an active booking | Valid active PNR, at least four hours before departure | Booking is cancelled and seats are released | H | PASS |
| TC-CAN-002 | FR-08 | Reject an unknown PNR | Invalid/unknown PNR | Clear invalid-PNR error appears | H | PASS |
| TC-CAN-003 | FR-08 | Reject a second cancellation | PNR already cancelled | Repeated cancellation is rejected | H | PASS |
| TC-CAN-004 | BR-02 | Enforce the four-hour cancellation cutoff | Request cancellation less than four hours before departure | Cancellation is rejected | H | PASS |
| TC-REF-001 | FR-07 | Show refund before confirmation | Eligible active booking | Refund amount is available before final cancellation (function level; no screen yet) | M | PASS |
| TC-REF-002 | FR-07 | Passenger declines cancellation | Passenger selects “keep booking” | Booking remains active and seats are not released. Previewing the refund does not change the booking (tested); the confirmation step needs a screen | M | PLANNED |
| TC-REF-003 | FR-07 / BR-02 | Apply refund rule after departure | Train departure time has passed | Cancellation is refused by BR-02, so no refund is paid; calculate_refund returns 0 after departure (deviation log #6) | M | PASS |
| TC-DATA-001 | NFR-04 | Reuse a seat immediately after cancellation | Cancel a booking, then query availability/book | Newly released seat is visible to the next request | H | PASS |
| TC-USE-001 | NFR-02 | First-time passenger completes search | Usable search interface available | User can complete a search without external help and understand errors | M | PLANNED |
| TC-DATA-002 | NFR-05 | Data survives a restart | Save a train and availability, close and reopen the database | Data is still present (storage layer) | H | PASS |
| TC-REG-001 | FR-09 | Register with valid details | Name, unique email, password of 8+ characters with a letter and a digit | Account is created | H | PASS |
| TC-REG-002 | FR-09 | Reject invalid registration input | Empty name, bad email, short or letter-only password | Rejected with a clear message; nothing is stored | H | PASS |
| TC-REG-003 | FR-09 | Reject a duplicate email | Email already registered, including in a different letter case | Registration is rejected | H | PASS |
| TC-LOGIN-001 | FR-10 | Log in with correct credentials | Registered email and password | A session token is returned | H | PASS |
| TC-LOGIN-002 | FR-10 | Wrong credentials give a generic error | Wrong password; unknown email | Same message for both, so the wrong field is not revealed | H | PASS |
| TC-LOGIN-003 | FR-10 | Logout ends the session | Logged-in session | The session is no longer valid | H | PASS |
| TC-SEC-001 | SR-01 | Passwords stored only as salted hashes | Register an account and inspect the stored value | No plain-text password; the same password gives different hashes | H | PASS |
| TC-SEC-002 | SR-02 | Admin functions only for admins | Passenger session tries an admin function | Access is denied | H | PLANNED |
| TC-SEC-003 | SR-02 | A passenger sees only their own bookings | Passenger uses another passenger's PNR | The request is refused | H | PLANNED |
| TC-PNR-001 | FR-11 | View a booking by PNR | Existing PNR | Train, date, class, passengers, fare and status are shown | M | PLANNED |
| TC-PNR-002 | FR-11 | View a booking with an unknown PNR | PNR that does not exist | Error message is shown | M | PLANNED |
| TC-HIST-001 | FR-12 | List own bookings | Passenger with bookings | Only that passenger's bookings are listed | M | PLANNED |
| TC-HIST-002 | FR-12 | Passenger with no bookings | New passenger | A "no bookings" message is shown | M | PLANNED |
| TC-ADM-001 | FR-13 | Admin adds a valid train | All required fields | Train is saved and appears in search | H | PLANNED |
| TC-ADM-002 | FR-13 | Reject a duplicate train number or missing fields | Existing train number; empty required field | Rejected with a clear message | H | PLANNED |
| TC-ADM-003 | FR-14 | Admin updates a train | Change the schedule | Search shows the new details | M | PLANNED |
| TC-ADM-004 | FR-14 | Remove a train that has active bookings | Train with a confirmed booking | Removal is refused with an explanation | M | PLANNED |
| TC-ADM-005 | FR-15 | Admin views all bookings | Admin session | All bookings are listed | M | PLANNED |
| TC-ADM-006 | FR-15 | Admin filters bookings | Filter by train, date or PNR | Only matching bookings are shown | M | PLANNED |

**Note:** Search, availability, booking, PNR, seat-allocation, traveller-check, cancellation, refund, registration, login and password-hashing cases are marked PASS because automated tests cover them and pass. The test names in `tests/` do not carry these IDs, so the link between a case and its test is made here. View-booking, administration, access-control and screen-based cases stay PLANNED until the features exist and have been run. The refund slabs in BR-02 are fixed in `docs/requirements.md` and recorded in the deviation log.

# Test Cases — Railway Reservation System

**Baseline date:** 12 October 2026  
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
| TC-AVAIL-001 | FR-02 | Show seat counts by class | Valid train/date; availability module implemented | Available seats are shown per class | H | PLANNED |
| TC-AVAIL-002 | FR-02 | Handle a full class | Selected class has zero seats | Waiting-list/not-available message appears | H | PLANNED |
| TC-BOOK-001 | FR-04 | Book when seats are available | Valid passenger details and available class | Booking succeeds and a unique PNR is displayed | H | PLANNED |
| TC-BOOK-002 | FR-04 | Update availability after booking | Book two seats | Available count decreases by two | H | PLANNED |
| TC-BOOK-003 | FR-05 | Reject empty passenger name | Name = empty string | Booking is rejected with a field-specific error | M | PLANNED |
| TC-BOOK-004 | FR-05 | Reject invalid passenger age | Age = 0 or 121 | Booking is rejected with an age validation error | M | PLANNED |
| TC-BOOK-005 | BR-01 | Reject more than six passengers | Seven passengers in one booking | Booking is rejected; maximum remains six | H | PLANNED |
| TC-BOOK-006 | NFR-03 | Two users attempt to book the final seat | Two simultaneous requests; one seat remaining | Exactly one booking succeeds; the other receives no-seat response | H | PLANNED |
| TC-CAN-001 | FR-06 | Cancel an active booking | Valid active PNR, at least four hours before departure | Booking is cancelled and seats are released | H | PLANNED |
| TC-CAN-002 | FR-08 | Reject an unknown PNR | Invalid/unknown PNR | Clear invalid-PNR error appears | H | PLANNED |
| TC-CAN-003 | FR-08 | Reject a second cancellation | PNR already cancelled | Repeated cancellation is rejected | H | PLANNED |
| TC-CAN-004 | BR-02 | Enforce the four-hour cancellation cutoff | Request cancellation less than four hours before departure | Cancellation is rejected | H | PLANNED |
| TC-REF-001 | FR-07 | Show refund before confirmation | Eligible active booking | Refund amount is shown before final cancellation | M | PLANNED |
| TC-REF-002 | FR-07 | Passenger declines cancellation | Passenger selects “keep booking” | Booking remains active and seats are not released | M | PLANNED |
| TC-REF-003 | FR-07 / BR-02 | Apply refund rule after departure | Train departure time has passed | No refund is given; exact cancellation behaviour follows confirmed requirement | M | PLANNED |
| TC-DATA-001 | NFR-04 | Reuse a seat immediately after cancellation | Cancel a booking, then query availability/book | Newly released seat is visible to the next request | H | PLANNED |
| TC-USE-001 | NFR-02 | First-time passenger completes search | Usable search interface available | User can complete a search without external help and understand errors | M | PLANNED |

**Note:** The existing automated suite contains the 13 search/validation checks marked PASS. The remaining cases must not be marked as passed until their corresponding features are available and the tests are run. The refund slabs in BR-02 are still TBD in the source requirements.

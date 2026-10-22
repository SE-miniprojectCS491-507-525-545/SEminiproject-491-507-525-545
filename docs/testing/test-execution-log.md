# Test Execution Log — Railway Reservation System

**Execution date:** 22 October 2026  
**Baseline:** `main` at commit `b2861ee` with the integration-fix patch applied  
**Command:** `python -m pytest --cov=src --cov-branch --cov-fail-under=80`  
**Environment:** Python 3.12.3 (Linux); pytest 9.1.1  
**Run by:** review environment. Re-run on a team machine before the demo and update the environment line if it differs.

## Result

**215 passed, 0 failed.** Coverage 99.6% (the CI minimum is 80%).

| Area | Executed | Passed | Failed |
|---|---:|---:|---:|
| Train search and input validation | 56 | 56 | 0 |
| Seat availability (and search-to-availability flow) | 34 | 34 | 0 |
| Cancellation, deadline and refund | 34 | 34 | 0 |
| Registration, login and password security | 39 | 39 | 0 |
| Data model, storage and cross-module checks | 52 | 52 | 0 |
| Performance and usability | 0 | 0 | 0 |

## Test evidence

The suite checks train search and its input validation, seat availability by class, cancellation by PNR, the 4-hour deadline and the refund fee, registration, login and logout, password hashing, the SQLite storage layer (including the rule that two bookings cannot hold the same seat), all-or-nothing cancellation, and checks that modules written by different people work together.

## Not executed

TC-SEARCH-014 (search time of 5 seconds), TC-USE-001 (usability), booking and concurrency cases (TC-BOOK-001 to 006), the confirmation step of TC-REF-002, and all view-booking, administration and access-control cases remain planned because the features or screens are not built yet.

## Defect observation

One real defect was found and fixed: a booking that had no availability row could raise the free-seat count wrongly after cancellation. Cancellation through `cancel_booking` now updates the status, the seat count and the seat numbers in a single step. This is not evidence that the unbuilt features are defect-free.

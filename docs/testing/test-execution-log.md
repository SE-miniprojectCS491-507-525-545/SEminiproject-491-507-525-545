# Test Execution Log — Railway Reservation System

**Execution date:** 24 October 2026  
**Baseline:** `main` at commit `1ae7a7c` with the FR-04 booking branch applied  
**Command:** `python -m pytest --cov=src --cov-branch --cov-fail-under=80`  
**Environment:** Python 3.12.3 (Linux); pytest 9.1.1  
**Run by:** review environment. Re-run on a team machine before the demo and update the environment line if it differs.

## Result

**286 passed, 0 failed.** Coverage 99.70% (the CI minimum is 80%).

| Area | Executed | Passed | Failed |
|---|---:|---:|---:|
| Train search and input validation | 56 | 56 | 0 |
| Seat availability (and search-to-availability flow) | 34 | 34 | 0 |
| Booking, PNR, seat allocation and traveller checks | 68 | 68 | 0 |
| Cancellation, deadline and refund | 34 | 34 | 0 |
| Registration, login and password security | 39 | 39 | 0 |
| Data model, storage and cross-module checks | 55 | 55 | 0 |
| Performance and usability | 0 | 0 | 0 |

## Test evidence

The suite checks train search and its input validation, seat availability by class, booking with PNR generation, seat allocation and passenger checks (including two people booking the last seat at the same time, repeated 30 times without a failure), cancellation by PNR, the 4-hour deadline and the refund fee, registration, login and logout, password hashing, the SQLite storage layer, all-or-nothing booking and cancellation, and checks that modules written by different people work together.

## Not executed

TC-SEARCH-014 (search time of 5 seconds), TC-USE-001 (usability), the confirmation step of TC-REF-002, and all view-booking, administration and access-control cases remain planned because the features or screens are not built yet.

## Defect observation

One real defect was found and fixed earlier: a booking that had no availability row could raise the free-seat count wrongly after cancellation. Booking and cancellation now each update the status, the seat count and the seat numbers in a single step. This is not evidence that the unbuilt features are defect-free.

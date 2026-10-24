# Deviation Log

This file records every place where the built system differs from the submitted
SRS, SAD and Test Plan, and why. It is updated through Sprint 1 and Sprint 2 and
explained during the final demo.

| # | Document | What was specified | What was built | Reason | Status |
|---|----------|--------------------|----------------|--------|--------|
| 1 | SAD 4.3 (API Design) | REST-style endpoints, for example `POST /booking` and `POST /cancellation` | Each service is a Python module with plain functions (`cancel_ticket`, `register_passenger`, `login`), with no HTTP server | Console/module application is enough for the course scope and the sprint timeline. The interface (inputs, outputs, errors) matches the SAD. | Confirm |
| 2 | SAD 3.6 (Data Store) | SQLite | `storage.py` (SQLite) is built and used by search and availability. Registration, login and the dictionary-based `cancel_ticket` still keep their data in dictionaries passed into the functions. `cancel_booking` is the database version of cancellation | Built the logic first so it could be tested without a database, then added storage (TASK-01). | Open until registration, login and booking use `storage.py` (NFR-05) |
| 3 | SAD 3.3 and 3.4 (Components) | Components: Search, Booking, Cancellation, Admin | Three more modules added: `registration.py`, `auth.py`, `security.py` (FR-09, FR-10, SR-01) | The SAD listed login and registration under Open Issues (4.6). They were added to the backlog afterwards. | Done |
| 4 | SRS BR-02 (Refund) | Refund percentage depends on time before departure. Slabs marked TBD, with an example of 100% / 50% / 0% | Fee is 10% of the fare when cancelling more than 24 hours before departure, and 50% from 24 hours down to 4 hours (refund 90% and 50%) | The SRS left the figures open, so the team agreed these. `docs/requirements.md` BR-02 now states them. | Confirm the figures with the team |
| 5 | SRS BR-02 (Deadline) | Cancellation allowed "up to 4 hours before departure" | Exactly 4 hours is allowed. Anything closer than 4 hours is refused | Reads "up to 4 hours" as including the 4-hour mark. | Done |
| 6 | SRS FR-07 and BR-02 (no refund after departure) | A cancellation after departure gets no refund | A cancellation inside the last 4 hours, including after departure, is **refused** by BR-02, so it never reaches the refund step. `calculate_refund` still returns 0 after departure | BR-02 and FR-07 overlap. Refusing the cancellation covers both. | Done |
| 7 | Process | One repository | The team moved to a new repository. Issue numbers changed. Earlier pull requests (#3 and #25 to #29) remain in the original repository, which is kept unchanged | Repository was reorganised at the start of Sprint 1. | Done |
| 8 | SRS FR-09 and User Story 6 (Registration) | Name, email **or phone**, and password; a duplicate email or phone is rejected | Name, email and password only. A duplicate email is rejected. There is no phone field | Email is enough to identify an account for the demo. Phone can be added later. | Confirm with the team |
| 9 | SRS FR-02 (Seat availability) | Shows seats per class, with a full class shown as "Waiting list" or "Not available" | A full class is reported as sold out (0 free seats). There is no waiting list | Waiting list is outside the agreed scope (User Story 10 is still in the backlog). | Confirm with the team |
| 10 | Sprint 1 plan (booking calls `inventory.reserve`) | Booking calls a separate reserve step in the availability code | Seats are reserved inside the booking's own database step (`storage.book_seats`). There is no separate `reserve` function | A separate call would be a second save, so a failure between the two could lose seats. One step keeps FR-04, NFR-03 and NFR-04 correct. | Done. Tell the team no `reserve` is needed |

## Notes

- Delete any row that turns out not to apply, and add a row whenever the built
  system differs from a submitted document.
- Rows marked "Confirm" need a quick check with the team before the demo.
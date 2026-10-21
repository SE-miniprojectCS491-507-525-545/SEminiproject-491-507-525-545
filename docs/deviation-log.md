# Deviation Log

This file records every place where the built system differs from the submitted
SRS, SAD and Test Plan, and why. It is updated through Sprint 1 and Sprint 2 and
explained during the final demo.

| # | Document | What was specified | What was built | Reason | Status |
|---|----------|--------------------|----------------|--------|--------|
| 1 | SAD 4.3 (API Design) | REST-style endpoints, for example `POST /booking` and `POST /cancellation` | Each service is a Python module with plain functions (`cancel_ticket`, `register_passenger`, `login`), with no HTTP server | Console/module application is enough for the course scope and the sprint timeline. The interface (inputs, outputs, errors) matches the SAD. | Confirm |
| 2 | SAD 3.6 (Data Store) | SQLite | Bookings, passengers and seat counts are held as dictionaries passed into the functions. Persistence is tracked separately as NFR-05 | Built the logic first so it can be tested without a database. | Open until NFR-05 is done |
| 3 | SAD 3.3 and 3.4 (Components) | Components: Search, Booking, Cancellation, Admin | Three more modules added: `registration.py`, `auth.py`, `security.py` (FR-09, FR-10, SR-01) | The SAD listed login and registration under Open Issues (4.6). They were added to the backlog afterwards. | Done |
| 4 | SRS FR-07 (Refund) | "Deduct a cancellation fee" with no amount given | Fee is 10% of the fare when cancelling more than 24 hours before departure, and 50% from 24 hours down to 4 hours | The SRS gave no figure, so the team agreed one. | Confirm the figures with the team |
| 5 | SRS BR-02 (Deadline) | Cancellation allowed "up to 4 hours before departure" | Exactly 4 hours is allowed. Anything closer than 4 hours is refused | Reads "up to 4 hours" as including the 4-hour mark. | Done |
| 6 | SRS FR-07 ("no refund after departure") | A cancellation after departure gets no refund | A cancellation inside the last 4 hours, including after departure, is **refused** by BR-02, so it never reaches the refund step. `calculate_refund` still returns 0 after departure | BR-02 and FR-07 overlap. Refusing the cancellation covers both. | Done |
| 7 | Process | One repository | The team moved to a new repository. Issue numbers changed. Earlier pull requests (#3 and #25 to #29) remain in the original repository, which is kept unchanged | Repository was reorganised at the start of Sprint 1. | Done |

## Notes

- Delete any row that turns out not to apply, and add a row whenever the built
  system differs from a submitted document.
- Rows marked "Confirm" need a quick check with the team before the demo.
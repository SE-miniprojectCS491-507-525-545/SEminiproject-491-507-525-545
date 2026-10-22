# Railway Reservation System

## About the Project

The **Railway Reservation System** is a software application designed to simplify the process of searching for trains, checking seat availability, booking tickets, and managing railway reservations.

The system will provide functionality for passengers to search for suitable trains and manage their bookings, while administrators will be able to manage relevant railway and reservation information.

The project is being developed using **Python** and follows an Agile software development approach.

## Team Members

| Name       | SRN       |
| ---------- | --------- |
| `Tanisha Mathur` | `PES1UG24CS491` |
| `Urav B S` | `PES1UG24CS507` |
| `Vennela Shakthi V P` | `PES1UG24CS525` |
| `Yashas Shivarajappa` | `PES1UG24CS545` |


## Features and Status

| Area | Requirements | Status |
|------|--------------|--------|
| Shared data model and SQLite storage | TASK-01, NFR-05 (storage layer) | Done |
| Train search | FR-01, FR-03 | Done |
| Seat availability | FR-02 | Done |
| Cancellation (cancel by PNR, validation) | FR-06, FR-08 | Done |
| Cancellation (4-hour deadline, refund) | BR-02, FR-07 | Done |
| Registration and password hashing | FR-09, SR-01 | Done |
| Login and logout | FR-10 | Done |
| Booking, PNR, seat allocation | FR-04, FR-05, BR-01 | In progress |
| View booking by PNR, booking history | FR-11, FR-12 | Not started |
| Administration | FR-13, FR-14, FR-15 | Not started |
| Role-based access control | SR-02 | Not started |

## Getting Started

You need Python 3 installed. Then run these commands one at a time:

    git clone https://github.com/SE-miniprojectCS491-507-525-545/SEminiproject-491-507-525-545.git
    cd SEminiproject-491-507-525-545
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements-dev.txt
    python -m pytest

On Windows, activate the environment with `.venv\Scripts\activate` instead of the `source` line.

The database is a single SQLite file, `railway.db`, created in the project folder the first time the program connects. It is ignored by git. Set the `RAILWAY_DB` environment variable to use a different file.

## Project Structure

- src/railway/ : application code
  - models.py : shared data classes (Train, SeatClass, Passenger, Traveller, Booking)
  - storage.py : all SQLite code (tables, saving and loading, atomic cancellation)
  - dates.py : shared date parsing
  - search.py : train search and input validation
  - availability.py : seat availability
  - cancellation.py : cancellation, 4-hour deadline and refund
  - registration.py, auth.py, security.py : registration, login and password hashing
- tests/ : pytest unit and integration tests
- docs/ : requirements, user stories, SAD, SRS, test plan, deviation log
- .github/ : CI configuration

## Documentation

- Requirements and user stories: see the docs/ folder
- Differences between the built system and the submitted documents: docs/deviation-log.md

## Workflow

We work in Agile sprints. Each issue gets its own branch, a pull request, a review by the repo owner, and a merge into main. Sprint demo videos are stored in the repository.
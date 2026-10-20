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
| Train search | FR-01, FR-03 | Done |
| Cancellation (cancel by PNR, validation) | FR-06, FR-08 | Done |
| Cancellation (4-hour deadline, refund) | BR-02, FR-07 | In review |
| Registration and password hashing | FR-09, SR-01 | In review |
| Login and logout | FR-10 | In review |
| Booking, seat allocation, persistence | FR-04, NFR-05 | In progress |

## Getting Started

You need Python 3 installed. Then run these commands one at a time:

    git clone https://github.com/SE-miniprojectCS491-507-525-545/SEminiproject-491-507-525-545.git
    cd SEminiproject-491-507-525-545
    pip install -r requirements-dev.txt
    python -m pytest

## Project Structure

- src/railway/ : application code (search, cancellation, registration, auth, security)
- tests/ : pytest unit tests
- docs/ : requirements, user stories, SAD, SRS, test plan, deviation log
- .github/ : CI configuration

## Documentation

- Requirements and user stories: see the docs/ folder
- Differences between the built system and the submitted documents: docs/deviation-log.md

## Workflow

We work in Agile sprints. Each issue gets its own branch, a pull request, a review by the repo owner, and a merge into main. Sprint demo videos are stored in the repository.
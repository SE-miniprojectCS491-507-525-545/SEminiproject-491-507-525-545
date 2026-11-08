# Railway Reservation System

## About

The Railway Reservation System is a Python application for searching trains, checking seat availability, booking tickets and managing reservations. It provides a command-line interface (CLI) and a graphical interface built with Streamlit. Data is stored in SQLite.

## Team

| Name | SRN |
|---|---|
| Tanisha Mathur | PES1UG24CS491 |
| Urav B S | PES1UG24CS507 |
| Vennela Shakthi V P | PES1UG24CS525 |
| Yashas Shivarajappa | PES1UG24CS545 |

## Features

- Passenger registration, login and logout
- Train search by source, destination and travel date
- Seat availability and fare lookup
- Booking for 1–6 passengers with seat allocation
- Passenger booking history and PNR lookup
- Booking cancellation with refund calculation
- Admin-only train add, update and remove operations
- SQLite persistence
- Streamlit graphical interface and original CLI

## Requirements

- Python 3.10 or newer
- pip and Git
- Streamlit (installed through requirements.txt)

## Setup

Clone the repository:

\`\`\`bash
git clone https://github.com/SE-miniprojectCS491-507-525-545/SEminiproject-491-507-525-545.git
cd SEminiproject-491-507-525-545
\`\`\`

Create and activate a virtual environment.

**macOS / Linux**
\`\`\`bash
python3 -m venv .venv
source .venv/bin/activate
\`\`\`

**Windows PowerShell**
\`\`\`powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
\`\`\`

Install application dependencies:

\`\`\`bash
pip install -r requirements.txt
\`\`\`

For development and testing, install:

\`\`\`bash
pip install -r requirements-dev.txt
\`\`\`

## Run the Streamlit UI

Run from the repository root:

\`\`\`bash
PYTHONPATH=src streamlit run app.py
\`\`\`

Streamlit displays a local address, usually http://localhost:8501, which can be opened in a browser.

On Windows PowerShell:

\`\`\`powershell
$env:PYTHONPATH = "src"
streamlit run app.py
\`\`\`

The sidebar provides navigation. Passengers can register, log in, search trains, check seats, book tickets, view their bookings, look up a PNR and cancel eligible bookings. Administrators also see train-management controls.

### Demo data

Click **Load demo data** in the sidebar to add sample trains and a passenger account to an empty database. It does not overwrite existing train data.

Demo passenger:
- Email: demo@railway.com
- Password: demo12345

Use demo credentials only for demonstrations.

## Run the CLI

The original CLI remains available:

\`\`\`bash
PYTHONPATH=src python -m railway
\`\`\`

Seed demo data from the CLI:

\`\`\`bash
PYTHONPATH=src python -m railway --seed
\`\`\`

## Run tests

Install development dependencies, then run:

\`\`\`bash
PYTHONPATH=src python -m pytest
\`\`\`

Coverage report:

\`\`\`bash
PYTHONPATH=src python -m pytest --cov=railway --cov-report=term-missing
\`\`\`

## Database

The app creates railway.db in the repository root on first use. Git ignores this database file. To use a different database, set RAILWAY_DB before launching.

macOS / Linux:
\`\`\`bash
export RAILWAY_DB=/path/to/your/railway.db
\`\`\`

Windows PowerShell:
\`\`\`powershell
$env:RAILWAY_DB = "C:\path\to\railway.db"
\`\`\`

## Project structure

- app.py — Streamlit graphical interface
- src/railway/ — backend application logic and CLI
  - models.py — shared data models
  - storage.py — SQLite persistence
  - registration.py, auth.py, security.py — account and password handling
  - search.py, availability.py — train search and seat availability
  - booking.py, pnr.py, seats.py — ticket booking and seat allocation
  - booking_views.py — booking details and access checks
  - cancellation.py — cancellation and refund rules
  - cli.py — command-line interface
- tests/ — automated tests
- docs/ — requirements, design and testing documents
- .github/ — GitHub Actions workflows

## Team workflow

Each change is developed on a separate feature branch and submitted through a pull request for review before merging into main.

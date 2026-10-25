# Demo Video (TASK-05)

Video: sprint1_demo.mov in this folder

## What the video shows
- Search with an unknown station (validation), then a valid search
- Seat availability before and after booking
- Booking two passengers and receiving a PNR
- Viewing the booking, and error messages for invalid input
- Cancelling with a refund, and the seats being released
- Running the automated tests

## How to reproduce it
    rm -f railway.db
    PYTHONPATH=src python3 -m railway --seed

The menu then lists the steps. Use a travel date about a week ahead.

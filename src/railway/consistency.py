"""Consistency check for seat counts and seat numbers (NFR-04).

    problems = find_inconsistencies(conn)
    if problems:
        print("\\n".join(problems))

An empty list means the free-seat counts, the bookings and the seat numbers all
agree with each other.
"""
from railway.models import CONFIRMED


def find_inconsistencies(conn):
    """Return a list of plain-text problems; an empty list means all is well."""
    problems = []

    # 1. The free-seat count must equal: seats in the class - seats booked.
    counts = conn.execute(
        """
        SELECT k.train_number, k.travel_date, k.seat_class, sc.total_seats,
               a.free_seats AS shown, COALESCE(b.booked, 0) AS booked
        FROM (SELECT train_number, travel_date, seat_class FROM availability
              UNION
              SELECT train_number, travel_date, seat_class
              FROM bookings WHERE status = ?) AS k
        JOIN seat_classes sc
          ON sc.train_number = k.train_number AND sc.seat_class = k.seat_class
        LEFT JOIN availability a
          ON a.train_number = k.train_number AND a.travel_date = k.travel_date
         AND a.seat_class = k.seat_class
        LEFT JOIN (SELECT train_number, travel_date, seat_class, SUM(passengers) AS booked
                   FROM bookings WHERE status = ?
                   GROUP BY train_number, travel_date, seat_class) b
          ON b.train_number = k.train_number AND b.travel_date = k.travel_date
         AND b.seat_class = k.seat_class
        ORDER BY k.train_number, k.travel_date, k.seat_class
        """,
        (CONFIRMED, CONFIRMED),
    ).fetchall()
    for row in counts:
        expected = row["total_seats"] - row["booked"]
        shown = row["total_seats"] if row["shown"] is None else row["shown"]
        if shown != expected:
            problems.append(
                f"Train {row['train_number']} on {row['travel_date']} ({row['seat_class']}): "
                f"shows {shown} free seat(s) but {row['booked']} of {row['total_seats']} "
                f"are booked, so {expected} should be free.")

    # 2. A confirmed booking holds one seat number per passenger; a cancelled one holds none.
    holders = conn.execute(
        """
        SELECT b.pnr, b.status, b.passengers, COUNT(s.seat_number) AS held
        FROM bookings b LEFT JOIN seat_allocations s ON s.pnr = b.pnr
        GROUP BY b.pnr ORDER BY b.pnr
        """
    ).fetchall()
    for row in holders:
        wanted = row["passengers"] if row["status"] == CONFIRMED else 0
        if row["held"] != wanted:
            problems.append(
                f"Booking {row['pnr']} ({row['status']}) holds {row['held']} seat number(s) "
                f"but should hold {wanted}.")

    # 3. A seat number cannot be higher than the number of seats in the class.
    too_high = conn.execute(
        """
        SELECT s.pnr, s.seat_number, sc.total_seats
        FROM seat_allocations s
        JOIN bookings b ON b.pnr = s.pnr
        JOIN seat_classes sc
          ON sc.train_number = b.train_number AND sc.seat_class = b.seat_class
        WHERE s.seat_number > sc.total_seats
        ORDER BY s.pnr, s.seat_number
        """
    ).fetchall()
    for row in too_high:
        problems.append(
            f"Booking {row['pnr']} holds seat {row['seat_number']} but the class has "
            f"only {row['total_seats']} seats.")

    return problems


def is_consistent(conn):
    return not find_inconsistencies(conn)

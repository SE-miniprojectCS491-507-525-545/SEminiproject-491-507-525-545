"""Seat allocation (FR-04c): which seat numbers a booking gets."""


class SeatAllocationError(ValueError):
    """Raised when the requested seats cannot be allocated."""


def allocate_seats(taken, total_seats, count):
    """Return the `count` lowest seat numbers that are not in `taken`.

    Seats in a class are numbered 1..total_seats. Keeping to the lowest free
    numbers keeps one booking's seats close together.
    """
    if count < 1:
        raise SeatAllocationError("At least one seat is required.")
    taken = set(taken)
    free = [n for n in range(1, total_seats + 1) if n not in taken]
    if len(free) < count:
        raise SeatAllocationError(f"Only {len(free)} seat(s) can be allocated.")
    return free[:count]

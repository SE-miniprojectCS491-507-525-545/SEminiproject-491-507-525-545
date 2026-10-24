import pytest

from railway.seats import SeatAllocationError, allocate_seats


def test_gives_the_lowest_free_seats():
    assert allocate_seats([], 60, 3) == [1, 2, 3]


def test_skips_seats_already_taken():
    assert allocate_seats([1, 2, 4], 10, 3) == [3, 5, 6]


def test_fills_gaps_left_by_cancellations():
    assert allocate_seats([2, 3], 5, 2) == [1, 4]


def test_can_take_the_very_last_seat():
    assert allocate_seats(range(1, 10), 10, 1) == [10]


def test_asking_for_more_than_are_free_is_refused():
    with pytest.raises(SeatAllocationError, match="Only 1 seat"):
        allocate_seats([1, 2], 3, 2)


@pytest.mark.parametrize("count", [0, -1])
def test_at_least_one_seat_is_needed(count):
    with pytest.raises(SeatAllocationError):
        allocate_seats([], 10, count)


def test_taken_seats_outside_the_class_are_ignored():
    assert allocate_seats([99], 5, 2) == [1, 2]

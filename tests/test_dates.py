from datetime import date, datetime

import pytest

from railway.availability import AvailabilityError, check_availability
from railway.dates import to_date
from railway.search import SearchError, validate_search


class Boom(ValueError):
    pass


def test_to_date_accepts_date_datetime_and_text():
    assert to_date(date(2026, 11, 2)) == date(2026, 11, 2)
    assert to_date(datetime(2026, 11, 2, 9, 30)) == date(2026, 11, 2)
    assert to_date(" 2026-11-02 ") == date(2026, 11, 2)


@pytest.mark.parametrize("bad", [None, "", "   "])
def test_to_date_requires_a_value(bad):
    with pytest.raises(Boom, match="required"):
        to_date(bad, Boom)


@pytest.mark.parametrize("bad", ["02-11-2026", "2026-13-40", "tomorrow"])
def test_to_date_rejects_bad_text_with_the_given_error(bad):
    with pytest.raises(Boom, match=r"YYYY-MM-DD"):
        to_date(bad, Boom)


def test_search_and_availability_give_the_same_date_message():
    with pytest.raises(SearchError) as search_error:
        validate_search("A", "B", "nonsense", ["A", "B"], today=date(2026, 10, 21))
    from railway import storage
    conn = storage.connect(":memory:")
    with pytest.raises(AvailabilityError) as availability_error:
        check_availability(conn, "12627", "nonsense", "3AC")
    conn.close()
    # the date is read before the train is looked up, so both reach the shared message
    assert str(search_error.value) == str(availability_error.value)

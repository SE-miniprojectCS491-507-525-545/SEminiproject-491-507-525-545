from datetime import date

from railway.dates import to_date
from railway.models import Train  # shared model (re-exported for old imports)


class SearchError(ValueError):
    """Raised when a train search input is invalid."""


def _clean(value):
    return (value or "").strip().lower()


def _parse_date(value):
    return to_date(value, SearchError)


def stations_of(trains):
    """Every station that appears as a source or destination, sorted."""
    return sorted({name for t in trains for name in (t.source, t.destination)})


def validate_search(source, destination, travel_date, stations, today=None):
    """Validate search input (FR-03). Returns cleaned (source, destination)."""
    today = today or date.today()
    src, dst = _clean(source), _clean(destination)

    if not src:
        raise SearchError("Source station is required.")
    if not dst:
        raise SearchError("Destination station is required.")
    day = _parse_date(travel_date)

    known = {s.strip().lower() for s in stations}
    if src not in known:
        raise SearchError(f"Unknown station: {source}.")
    if dst not in known:
        raise SearchError(f"Unknown station: {destination}.")
    if src == dst:
        raise SearchError("Source and destination cannot be the same.")
    if day < today:
        raise SearchError("Travel date cannot be in the past.")
    return src, dst


def search_trains(source, destination, travel_date, trains, stations, today=None):
    """Return trains matching the search (FR-01). Empty list if none match.

    Results keep the order of `trains`. travel_date may be a date or
    'YYYY-MM-DD' text.
    """
    src, dst = validate_search(source, destination, travel_date, stations, today)
    day = _parse_date(travel_date)
    return [
        t for t in trains
        if t.source.lower() == src
        and t.destination.lower() == dst
        and day.weekday() in t.runs_on
    ]
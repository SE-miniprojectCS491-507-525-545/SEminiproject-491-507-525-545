"""Helpers that make train search easy for a first-time user (NFR-02).

Pure functions (no input/output) so they are easy to test:
  * friendly_date()      - accepts 'today', 'tomorrow' as well as YYYY-MM-DD
  * suggest_stations()   - "Did you mean ...?" for a mistyped station
  * unknown_station_hint() / no_results_hint() - plain-English next steps
"""
import difflib
from datetime import date, timedelta

_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday")

DATE_PROMPT = "Travel date (YYYY-MM-DD, or 'today' / 'tomorrow'): "


def friendly_date(text, today=None):
    """Return a date from 'today', 'tomorrow' or 'YYYY-MM-DD'.

    Raises ValueError with the same wording the rest of the app uses.
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Travel date is required.")
    today = today or date.today()
    word = text.lower()
    if word == "today":
        return today
    if word == "tomorrow":
        return today + timedelta(days=1)
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValueError("Travel date must be in YYYY-MM-DD format.") from None


def suggest_stations(text, stations, limit=3):
    """Station names that look like what the user typed (typos, partial names)."""
    typed = (text or "").strip().lower()
    if not typed:
        return []
    by_lower = {s.lower(): s for s in stations}
    starts = [s for low, s in sorted(by_lower.items()) if low.startswith(typed)]
    close = [by_lower[m] for m in difflib.get_close_matches(typed, by_lower, n=limit, cutoff=0.6)]
    out = []
    for name in starts + close:
        if name not in out:
            out.append(name)
    return out[:limit]


def unknown_station_hint(text, stations):
    """One line to show after 'Unknown station'. Never empty."""
    matches = suggest_stations(text, stations)
    if matches:
        return "Did you mean: " + ", ".join(matches) + "?"
    return "Pick a station from the list above."


def _same(a, b):
    return a.strip().lower() == b.strip().lower()


def no_results_hint(trains, source, destination):
    """Explain WHY a search came back empty and what to try next."""
    on_route = [t for t in trains if _same(t.source, source) and _same(t.destination, destination)]
    if on_route:
        days = sorted({d for t in on_route for d in t.runs_on})
        return "This route runs on: " + ", ".join(_WEEKDAYS[d] for d in days) + ". Try one of those days."
    from_here = sorted({t.destination for t in trains if _same(t.source, source)})
    if from_here:
        return f"No trains run from {source.strip()} to {destination.strip()}. From {source.strip()} you can go to: " + ", ".join(from_here) + "."
    return f"No trains leave from {source.strip()}."
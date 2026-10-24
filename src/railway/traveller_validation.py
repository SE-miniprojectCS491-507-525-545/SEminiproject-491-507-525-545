"""Checks on the people travelling (FR-05) and the passenger limit (BR-01)."""
from railway.models import Traveller

MAX_TRAVELLERS = 6   # BR-01
MIN_AGE = 1
MAX_AGE = 120

_GENDERS = {"m": "M", "male": "M", "f": "F", "female": "F", "o": "O", "other": "O"}


class TravellerError(ValueError):
    """Raised when traveller details are invalid. The message names the field."""


def _clean_age(value, label):
    if isinstance(value, bool) or isinstance(value, float):
        age = None
    elif isinstance(value, int):
        age = value
    else:
        text = str(value).strip() if value is not None else ""
        age = int(text) if text.isdigit() else None
    if age is None or not MIN_AGE <= age <= MAX_AGE:
        raise TravellerError(
            f"{label}: age must be a whole number from {MIN_AGE} to {MAX_AGE}.")
    return age


def validate_travellers(travellers):
    """Return the travellers cleaned up (trimmed name, int age, M/F/O gender)."""
    travellers = list(travellers or [])
    if not travellers:
        raise TravellerError("At least one passenger is required.")
    if len(travellers) > MAX_TRAVELLERS:
        raise TravellerError(
            f"A booking can have at most {MAX_TRAVELLERS} passengers.")
    cleaned = []
    for number, person in enumerate(travellers, start=1):
        label = f"Passenger {number}"
        name = (person.name or "").strip()
        if not name:
            raise TravellerError(f"{label}: name is required.")
        age = _clean_age(person.age, label)
        gender = _GENDERS.get(str(person.gender or "").strip().lower())
        if gender is None:
            raise TravellerError(f"{label}: gender must be M, F or O.")
        cleaned.append(Traveller(name, age, gender))
    return cleaned

"""Checks on the people travelling (FR-05) and the passenger limit (BR-01)."""
import unicodedata

from railway.models import Traveller

MAX_TRAVELLERS = 6   # BR-01
MIN_AGE = 1
MAX_AGE = 120
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 50

_NAME_PUNCTUATION = " .'-"   # e.g. "J. R. Rao", "D'Souza", "Anne-Marie"
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


def _name_char_ok(ch):
    # isalnum() covers letters of every language; "M*" marks cover accents/vowel signs.
    return ch.isalnum() or ch in _NAME_PUNCTUATION or unicodedata.category(ch).startswith("M")


def _clean_name(value, label):
    name = " ".join((value or "").split())   # trim and collapse inner spaces
    if not name:
        raise TravellerError(f"{label}: name is required.")
    if not MIN_NAME_LENGTH <= len(name) <= MAX_NAME_LENGTH:
        raise TravellerError(
            f"{label}: name must be {MIN_NAME_LENGTH} to {MAX_NAME_LENGTH} characters.")
    if not all(_name_char_ok(ch) for ch in name):
        raise TravellerError(
            f"{label}: name can only contain letters, digits, spaces, . ' and -.")
    if not any(ch.isalpha() for ch in name):
        raise TravellerError(f"{label}: name must contain at least one letter.")
    if not name[0].isalnum():
        raise TravellerError(f"{label}: name must start with a letter or digit.")
    return name


def validate_traveller(person, number=1):
    """Validate ONE traveller and return it cleaned. `number` is used in messages."""
    label = f"Passenger {number}"
    name = _clean_name(person.name, label)
    age = _clean_age(person.age, label)
    gender = _GENDERS.get(str(person.gender or "").strip().lower())
    if gender is None:
        raise TravellerError(f"{label}: gender must be M, F or O.")
    return Traveller(name, age, gender)


def validate_travellers(travellers):
    """Return the travellers cleaned up (trimmed name, int age, M/F/O gender)."""
    travellers = list(travellers or [])
    if not travellers:
        raise TravellerError("At least one passenger is required.")
    if len(travellers) > MAX_TRAVELLERS:
        raise TravellerError(
            f"A booking can have at most {MAX_TRAVELLERS} passengers.")
    return [validate_traveller(person, number)
            for number, person in enumerate(travellers, start=1)]
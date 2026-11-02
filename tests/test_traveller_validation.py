import pytest

from railway.models import Traveller
from railway.traveller_validation import TravellerError, validate_travellers


def person(name="Asha Rao", age=30, gender="F"):
    return Traveller(name, age, gender)


def test_valid_travellers_are_returned_cleaned():
    cleaned = validate_travellers([person("  Asha Rao ", "30", "female")])
    assert cleaned == [Traveller("Asha Rao", 30, "F")]


@pytest.mark.parametrize("age", [1, 120])
def test_age_limits_are_allowed(age):
    assert validate_travellers([person(age=age)])[0].age == age


@pytest.mark.parametrize("age", [0, 121, -5, None, "", "abc", "12.5", 30.5, True])
def test_age_outside_1_to_120_or_not_a_whole_number_is_rejected(age):
    with pytest.raises(TravellerError, match=r"Passenger 1: age"):
        validate_travellers([person(age=age)])


@pytest.mark.parametrize("name", ["", "   ", None])
def test_empty_name_is_rejected(name):
    with pytest.raises(TravellerError, match=r"Passenger 1: name is required"):
        validate_travellers([person(name=name)])


@pytest.mark.parametrize("gender", ["", None, "x", "robot"])
def test_unknown_gender_is_rejected(gender):
    with pytest.raises(TravellerError, match=r"Passenger 1: gender"):
        validate_travellers([person(gender=gender)])


@pytest.mark.parametrize("given,expected", [("m", "M"), ("Male", "M"), ("F", "F"),
                                            ("other", "O"), (" O ", "O")])
def test_gender_is_normalised(given, expected):
    assert validate_travellers([person(gender=given)])[0].gender == expected


def test_six_passengers_are_allowed_and_seven_are_not():
    assert len(validate_travellers([person()] * 6)) == 6
    with pytest.raises(TravellerError, match="at most 6"):
        validate_travellers([person()] * 7)


@pytest.mark.parametrize("empty", [[], None])
def test_at_least_one_passenger_is_needed(empty):
    with pytest.raises(TravellerError, match="At least one"):
        validate_travellers(empty)


def test_error_names_the_passenger_that_is_wrong():
    with pytest.raises(TravellerError, match=r"Passenger 2: name"):
        validate_travellers([person(), person(name="")])


@pytest.mark.parametrize("name", ["Asha Rao", "D'Souza", "Anne-Marie", "J. R. Rao", "Ñandú Pérez", "பாலா"])
def test_real_world_names_are_accepted(name):
    assert validate_travellers([person(name=name)])[0].name == name


@pytest.mark.parametrize("name", ["!!!", "@sha", "Asha_Rao", "123", "A", "-Asha", "x" * 51])
def test_names_with_symbols_no_letters_or_bad_length_are_rejected(name):
    with pytest.raises(TravellerError, match=r"Passenger 1: name"):
        validate_travellers([person(name=name)])


def test_extra_spaces_inside_a_name_are_collapsed():
    assert validate_travellers([person(name="  Asha    Rao ")])[0].name == "Asha Rao"


def test_validate_traveller_checks_one_person_and_uses_their_number():
    from railway.traveller_validation import validate_traveller
    assert validate_traveller(person(gender="f"), 3).gender == "F"
    with pytest.raises(TravellerError, match=r"Passenger 3: age"):
        validate_traveller(person(age=0), 3)
import pytest

from railway.pnr import PNRError, generate_pnr


def test_pnr_is_ten_digits_and_never_starts_with_zero():
    for _ in range(200):
        pnr = generate_pnr(lambda p: False)
        assert len(pnr) == 10 and pnr.isdigit() and pnr[0] != "0"


def test_lowest_and_highest_possible_pnr():
    assert generate_pnr(lambda p: False, pick=lambda n: 0) == "1000000000"
    assert generate_pnr(lambda p: False, pick=lambda n: n - 1) == "9999999999"


def test_pnr_already_in_use_is_skipped():
    picks = iter([5, 5, 7])
    used = {"1000000005"}
    pnr = generate_pnr(lambda p: p in used, pick=lambda n: next(picks))
    assert pnr == "1000000007"


def test_gives_up_after_the_allowed_attempts():
    with pytest.raises(PNRError):
        generate_pnr(lambda p: True, attempts=3)

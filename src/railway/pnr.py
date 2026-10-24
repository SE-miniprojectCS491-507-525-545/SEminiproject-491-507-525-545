"""PNR generation (FR-04b).

A PNR is a 10-digit booking reference that never starts with 0, like the
numbers on real railway tickets. Uniqueness is checked against the database
through the `exists` function the caller passes in.
"""
import secrets

PNR_LENGTH = 10
_LOWEST = 10 ** (PNR_LENGTH - 1)           # 1000000000
_COUNT = 9 * 10 ** (PNR_LENGTH - 1)        # how many 10-digit numbers there are


class PNRError(RuntimeError):
    """Raised when no unused PNR could be found."""


def generate_pnr(exists, pick=secrets.randbelow, attempts=20):
    """Return a PNR for which exists(pnr) is False.

    `pick(n)` must return a number from 0 to n-1 (tests pass a fixed one).
    """
    for _ in range(attempts):
        pnr = str(_LOWEST + pick(_COUNT))
        if not exists(pnr):
            return pnr
    raise PNRError("Could not generate a unique PNR. Please try again.")

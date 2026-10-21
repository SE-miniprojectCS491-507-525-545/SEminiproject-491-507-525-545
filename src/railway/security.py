import hashlib
import hmac
import os

ITERATIONS = 200_000


def hash_password(password, salt=None):
    """Return 'salt$hash' (both hex) using PBKDF2-HMAC-SHA256 and a random salt (SR-01)."""
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    """Check a password against a stored 'salt$hash' value (SR-01)."""
    try:
        salt_hex, _ = stored.split("$")
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)
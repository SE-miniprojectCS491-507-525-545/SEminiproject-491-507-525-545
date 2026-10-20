from railway.security import hash_password, verify_password


def test_hash_is_not_the_plain_password():
    stored = hash_password("Secret123")
    assert "Secret123" not in stored
    assert "$" in stored


def test_same_password_gets_different_hashes_because_of_salt():
    assert hash_password("Secret123") != hash_password("Secret123")


def test_correct_password_verifies():
    assert verify_password("Secret123", hash_password("Secret123")) is True


def test_wrong_password_fails():
    assert verify_password("Wrong1234", hash_password("Secret123")) is False


def test_malformed_stored_value_fails_safely():
    assert verify_password("Secret123", "not-a-valid-hash") is False
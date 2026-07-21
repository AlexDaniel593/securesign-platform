from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        hashed = hash_password("Test1234!")
        assert isinstance(hashed, str)
        assert hashed != "Test1234!"

    def test_verify_password_correct(self):
        hashed = hash_password("Test1234!")
        assert verify_password("Test1234!", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("Test1234!")
        assert verify_password("WrongPass1!", hashed) is False

    def test_same_password_different_hashes(self):
        h1 = hash_password("Test1234!")
        h2 = hash_password("Test1234!")
        assert h1 != h2


class TestJWT:
    def test_create_access_token_returns_string(self):
        token = create_access_token({"sub": "1", "email": "test@test.com"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        token = create_access_token({"sub": "1", "email": "test@test.com"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["email"] == "test@test.com"

    def test_decode_invalid_token(self):
        result = decode_access_token("invalid.token.here")
        assert result is None

    def test_decode_expired_token(self):
        token = create_access_token(
            {"sub": "1"}, expires_delta=timedelta(seconds=-1)
        )
        payload = decode_access_token(token)
        assert payload is None

    def test_token_contains_claims(self):
        token = create_access_token({"sub": "42", "email": "user@test.com"})
        payload = decode_access_token(token)
        assert payload["sub"] == "42"
        assert payload["email"] == "user@test.com"
        assert "exp" in payload
        assert "iat" in payload

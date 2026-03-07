"""Unit tests for app/services/auth.py — no DB required."""

import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from jose import jwt

from app.config import settings
from app.services.auth import (
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)


# ── Password hashing ──────────────────────────────────────────────────────────


def test_hash_password_differs_from_plain():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert len(hashed) > 20


def test_verify_password_correct():
    hashed = hash_password("MyPassword!")
    assert verify_password("MyPassword!", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("correct-password")
    assert verify_password("wrong-password", hashed) is False


def test_hash_password_same_input_different_hashes():
    """bcrypt salts should make each hash unique."""
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2


# ── JWT creation ──────────────────────────────────────────────────────────────


def test_create_access_token_returns_string():
    token = create_access_token("user-id-1", "org-id-1")
    assert isinstance(token, str)
    assert len(token) > 10


def test_create_access_token_payload():
    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    token = create_access_token(user_id, org_id)

    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == user_id
    assert payload["org_id"] == org_id
    assert "exp" in payload
    assert "iat" in payload


# ── Token verification ────────────────────────────────────────────────────────


def test_verify_token_valid():
    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    token = create_access_token(user_id, org_id)

    result = verify_token(token)
    assert result is not None
    assert result["sub"] == user_id
    assert result["org_id"] == org_id


def test_verify_token_garbage_string():
    assert verify_token("not.a.valid.token") is None


def test_verify_token_empty_string():
    assert verify_token("") is None


def test_verify_token_expired():
    """Manually forge an already-expired token."""
    expired_payload = {
        "sub": "user-id",
        "org_id": "org-id",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        "iat": datetime.now(timezone.utc) - timedelta(hours=25),
    }
    expired_token = jwt.encode(
        expired_payload, settings.secret_key, algorithm=settings.jwt_algorithm
    )
    assert verify_token(expired_token) is None


def test_verify_token_wrong_secret():
    """A token signed with a different secret should be rejected."""
    payload = {
        "sub": "user-id",
        "org_id": "org-id",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    bad_token = jwt.encode(payload, "wrong-secret", algorithm=settings.jwt_algorithm)
    assert verify_token(bad_token) is None

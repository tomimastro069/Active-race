import pytest
from app.core import security

PASSWORD = "supersecretpass123!"

# --- Argon2id Password Hashing ---
def test_hash_and_verify_password_success():
    hash_ = security.hash_password(PASSWORD)
    assert isinstance(hash_, str)
    assert security.verify_password(PASSWORD, hash_)

def test_verify_password_fail():
    hash_ = security.hash_password(PASSWORD)
    assert not security.verify_password("wrongpassword", hash_)

# --- JWT Encoding/Decoding ---
def test_jwt_create_and_decode_roundtrip():
    data = {"sub": "user-1", "tenant_id": "tenant-42", "roles": ["admin"]}
    token = security.create_access_token(data, expires_minutes=5)
    decoded = security.decode_access_token(token)
    for key in data:
        assert decoded[key] == data[key]

def test_jwt_decode_tampered_token():
    data = {"sub": "user-2", "tenant_id": "tenant-x"}
    token = security.create_access_token(data, expires_minutes=5)
    tampered = token[::-1]  # Reverse string to break signature
    with pytest.raises(Exception):
        security.decode_access_token(tampered)

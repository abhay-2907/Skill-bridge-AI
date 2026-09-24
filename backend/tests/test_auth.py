import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_token

def test_password_hashing():
    pwd = "secretpassword123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_token_flow():
    payload = {"sub": "42"}
    token = create_access_token(payload)
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "42"
    assert decoded.get("type") == "access"

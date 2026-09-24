"""
CareerPilot AI — Security Module
===================================
What is this?
  JWT token creation/validation + password hashing.

Why JWT?
  JSON Web Tokens let the server be stateless — it doesn't store sessions.
  The client sends the token on every request; the server validates it locally.

How password hashing works:
  1. User registers with plaintext password
  2. bcrypt hashes it with a random salt (slow by design — resists brute force)
  3. Only the hash is stored in the DB
  4. On login, bcrypt compares plaintext against stored hash
  5. Original password is never recoverable from the hash

Interview questions you should know:
  Q: Why use bcrypt over MD5/SHA?
  A: bcrypt is intentionally slow (cost factor), making brute-force attacks impractical.
     MD5/SHA are fast — fine for checksums, terrible for passwords.

  Q: What is JWT? What does it contain?
  A: JSON Web Token = Header.Payload.Signature (base64url-encoded).
     Payload has claims like user_id, exp (expiry), iat (issued at).
     The signature is HMAC-SHA256(header + payload, secret_key).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

import bcrypt

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


# ── JWT Token creation ────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    The token contains:
    - sub: subject (user_id as string)
    - type: "access"
    - exp: expiry timestamp
    - iat: issued-at timestamp
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a longer-lived refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    Returns the payload dict if valid, None if expired or tampered.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

import os
import time
from datetime import datetime, timedelta, timezone
import jwt
import hashlib
import hmac

try:
    import bcrypt
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-jwt-key-change-in-production-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt (or PBKDF2 fallback)."""
    if _HAS_BCRYPT:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        salt = os.urandom(16).hex()
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return f"pbkdf2_sha256${salt}${derived.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored hash."""
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        if _HAS_BCRYPT:
            try:
                return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
            except Exception:
                return False
        return False
    elif hashed_password.startswith("pbkdf2_sha256$"):
        parts = hashed_password.split("$")
        if len(parts) == 3:
            salt, hash_val = parts[1], parts[2]
            derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
            return hmac.compare_digest(derived.hex(), hash_val)
    return False

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> dict | None:
    """Decodes and validates a signed JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

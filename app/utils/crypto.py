import os
from cryptography.fernet import Fernet

# Default key for development (MUST be overridden in production using ENCRYPTION_KEY)
_DEFAULT_KEY = "T5G7Uv5Y9pPq1XJdfk7D7h9kLmNpQrStUvWxYz01234="
_KEY = os.getenv("ENCRYPTION_KEY", _DEFAULT_KEY)
_fernet = Fernet(_KEY.encode())

def encrypt(text: str | None) -> str | None:
    if text is None:
        return None
    try:
        return _fernet.encrypt(text.encode("utf-8")).decode("ascii")
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")

def decrypt(ciphertext: str | None) -> str | None:
    if ciphertext is None:
        return None
    try:
        return _fernet.decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")

def encrypt_bytes(data: bytes | None) -> bytes | None:
    if data is None:
        return None
    try:
        return _fernet.encrypt(data)
    except Exception as e:
        raise ValueError(f"Byte encryption failed: {str(e)}")

def decrypt_bytes(data: bytes | None) -> bytes | None:
    if data is None:
        return None
    try:
        return _fernet.decrypt(data)
    except Exception as e:
        raise ValueError(f"Byte decryption failed: {str(e)}")

import hashlib

def hash_search_key(text: str | None) -> str | None:
    """Generates a deterministic SHA-256 hash for exact-match indexing."""
    if text is None:
        return None
    # Normalize email (lowercase, stripped) and hash with pepper/key
    normalized = text.strip().lower()
    return hashlib.sha256((normalized + _KEY).encode("utf-8")).hexdigest()


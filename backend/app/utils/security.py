"""
Security utilities for password hashing and field-level encryption.

Password hashing uses bcrypt directly. Symmetric encryption of API
credentials (OAuth tokens, third-party keys stored in the database)
uses Fernet, whose key is sourced from the application configuration.
"""

from __future__ import annotations

import bcrypt
from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

# ── Password hashing ─────────────────────────────────────────────────────


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return ``True`` if *plain_password* matches the stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


# ── Fernet encryption for API credentials ────────────────────────────────

_fernet = Fernet(settings.ENCRYPTION_KEY.encode())


def encrypt_data(plaintext: str) -> str:
    """Encrypt *plaintext* and return a URL-safe base-64 encoded string.

    The returned ciphertext is safe to store in a ``VARCHAR`` / ``TEXT``
    database column.
    """
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_data(ciphertext: str) -> str:
    """Decrypt a value previously produced by :func:`encrypt_data`.

    Raises
    ------
    ValueError
        If the ciphertext is invalid or has been tampered with.
    """
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError(
            "Unable to decrypt data: the ciphertext is invalid or the "
            "encryption key has changed."
        ) from exc

"""
Authentication and user-management service layer.

Handles JWT creation / verification, user authentication, and new-user
registration (including the associated Organisation record).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import Organization, User
from app.schemas.user import TokenResponse, UserCreate
from app.utils.security import get_password_hash, verify_password

# ── JWT configuration ─────────────────────────────────────────────────────

ALGORITHM: str = "HS256"


# ── Token helpers ─────────────────────────────────────────────────────────


def create_access_token(data: dict[str, Any]) -> str:
    """Create a short-lived JWT access token.

    The ``"exp"`` claim is set to *now + ACCESS_TOKEN_EXPIRE_MINUTES*
    (from application settings).

    Parameters
    ----------
    data:
        Payload claims to include in the token (e.g. ``{"sub": user_id}``).

    Returns
    -------
    str
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a long-lived JWT refresh token.

    The ``"exp"`` claim is set to *now + REFRESH_TOKEN_EXPIRE_DAYS*
    (from application settings).

    Parameters
    ----------
    data:
        Payload claims to include in the token (e.g. ``{"sub": user_id}``).

    Returns
    -------
    str
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Parameters
    ----------
    token:
        The encoded JWT string.

    Returns
    -------
    dict
        The decoded payload.

    Raises
    ------
    ValueError
        If the token is expired, malformed, or fails signature verification.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError as exc:
        raise ValueError(f"Invalid or expired token: {exc}") from exc


# ── Convenience wrapper (preserves backward compatibility) ────────────────


def create_tokens(user_id: str) -> TokenResponse:
    """Generate an access + refresh token pair for a given user ID."""
    return TokenResponse(
        access_token=create_access_token({"sub": user_id}),
        refresh_token=create_refresh_token({"sub": user_id}),
    )


# ── User authentication ──────────────────────────────────────────────────


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    """Validate credentials and return the user if they match.

    Parameters
    ----------
    db:
        Active database session.
    email:
        The email address provided at login.
    password:
        The plaintext password to verify.

    Returns
    -------
    User | None
        The authenticated :class:`User` instance, or ``None`` if the email
        does not exist or the password is incorrect.
    """
    user: User | None = db.query(User).filter(User.email == email).first()
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ── User creation ────────────────────────────────────────────────────────


def create_user(db: Session, user_data: UserCreate) -> User:
    """Register a new user together with their organisation.

    The function creates an :class:`Organization` record first, then the
    :class:`User` record linked to it.

    Parameters
    ----------
    db:
        Active database session.
    user_data:
        Validated registration payload.

    Returns
    -------
    User
        The newly created user (already committed and refreshed).

    Raises
    ------
    ValueError
        If a user with the same email already exists.
    """
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing is not None:
        raise ValueError(f"A user with email '{user_data.email}' already exists.")

    # Create the organisation
    organization = Organization(name=user_data.organization_name)
    db.add(organization)
    db.flush()  # populate organization.id without committing

    # Create the user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        organization_id=organization.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ── Backward-compatible aliases ──────────────────────────────────────────


def register_user(db: Session, payload: UserCreate) -> tuple[User, TokenResponse]:
    """Create a new user and organization, returning the user and tokens."""
    user = create_user(db, payload)
    tokens = create_tokens(user.id)
    return user, tokens


def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse:
    """Validate a refresh token and return a new token pair."""
    try:
        payload = verify_token(refresh_token)
    except ValueError as exc:
        raise ValueError("Invalid refresh token") from exc

    if payload.get("type") != "refresh":
        raise ValueError("Not a refresh token")

    user_id: str = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise ValueError("User not found")

    return create_tokens(user.id)

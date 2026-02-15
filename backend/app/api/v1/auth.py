"""Authentication endpoints: register, login, refresh, password reset, and current user."""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.config import settings
from app.models.user import User
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.auth_service import (
    ALGORITHM,
    authenticate_user,
    create_tokens,
    refresh_access_token,
    register_user,
)
from app.utils.security import get_password_hash

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    """Create a new user and organization, then return tokens (auto-login)."""
    try:
        _user, tokens = register_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return tokens


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """OAuth2-compatible login (form fields: username=email, password)."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return create_tokens(user.id)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: TokenRefresh, db: Session = Depends(get_db)) -> TokenResponse:
    """Exchange a valid refresh token for a new access + refresh pair."""
    try:
        return refresh_access_token(db, body.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_active_user)) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)


# ── Password reset ──────────────────────────────────────────────────────


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    body: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Request a password reset email.

    Always returns 202 to avoid leaking whether the email exists.
    In production, this sends an email with a reset link.
    In dev/demo mode, the reset token is returned directly.
    """
    user: User | None = db.query(User).filter(User.email == body.email).first()

    if not user:
        # Don't leak whether the email exists
        return {"message": "If the email exists, a reset link has been sent."}

    # Generate a short-lived reset token (15 minutes)
    reset_token = jwt.encode(
        {
            "sub": user.id,
            "type": "password_reset",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )

    # Try to send email; fall back to logging the token
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    try:
        from app.utils.notifications import _notification_service

        sent = _notification_service.send_email(
            to_email=user.email,
            subject="Energy Autopilot - Reinitialisation de votre mot de passe",
            body_html=(
                f"<h2>Reinitialisation de mot de passe</h2>"
                f"<p>Bonjour {user.full_name or user.email},</p>"
                f"<p>Cliquez sur le lien ci-dessous pour reinitialiser votre mot de passe :</p>"
                f'<p><a href="{reset_url}">Reinitialiser mon mot de passe</a></p>'
                f"<p>Ce lien est valide pendant 15 minutes.</p>"
                f"<p>Si vous n'avez pas demande cette reinitialisation, ignorez cet email.</p>"
            ),
        )
        if not sent:
            logger.info("Password reset token (SMTP not configured): %s", reset_token)
    except Exception:
        logger.info("Password reset token (email failed): %s", reset_token)

    # In dev/mock mode, also return the token for convenience
    if settings.MOCK_APIS:
        return {
            "message": "If the email exists, a reset link has been sent.",
            "debug_token": reset_token,
            "debug_reset_url": reset_url,
        }

    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/password-reset/confirm")
def confirm_password_reset(
    body: PasswordResetConfirm,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Validate the reset token and set a new password."""
    from jose import JWTError

    try:
        payload = jwt.decode(body.token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    if payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type.",
        )

    user_id = payload.get("sub")
    user: User | None = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user.hashed_password = get_password_hash(body.new_password)
    db.commit()

    logger.info("Password reset completed for user %s", user.email)
    return {"message": "Password has been reset successfully."}

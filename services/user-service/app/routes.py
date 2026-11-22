from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RefreshToken
from app.schemas import UserCreate, UserLogin, UserResponse, Token, RefreshRequest
from app.auth import (
    hash_password, verify_password, create_access_token, get_current_user,
    generate_refresh_token, hash_refresh_token, REFRESH_TOKEN_EXPIRE_DAYS,
)

router = APIRouter()


def _issue_tokens(user: User, db: Session) -> dict:
    """Create a fresh access token + a fresh refresh token (stored hashed)."""
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "is_admin": user.is_admin}
    )
    raw_refresh = generate_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    db.commit()
    return {"access_token": access_token, "refresh_token": raw_refresh, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email or username already registered")

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _issue_tokens(user, db)


@router.post("/refresh", response_model=Token)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """
    Exchange a valid refresh token for a NEW access token + NEW refresh token.
    The old refresh token is revoked immediately (rotation). If a token that was
    already used/revoked is presented again, someone may have stolen it, so we
    revoke every session for that user (reuse detection).
    """
    invalid = HTTPException(status_code=401, detail="Invalid or expired refresh token")

    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_refresh_token(body.refresh_token)
    ).first()
    if not record:
        raise invalid

    if record.revoked:
        db.query(RefreshToken).filter(
            RefreshToken.user_id == record.user_id, RefreshToken.revoked == False  # noqa: E712
        ).update({"revoked": True})
        db.commit()
        raise invalid

    expires_at = record.expires_at
    if expires_at.tzinfo is None:  # sqlite returns naive datetimes
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise invalid

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise invalid

    record.revoked = True
    db.commit()
    # is_admin is re-read from the DB here, so role changes apply on the next refresh.
    return _issue_tokens(user, db)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    """Revoke this refresh token. Idempotent: unknown tokens are silently ignored."""
    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_refresh_token(body.refresh_token)
    ).first()
    if record and not record.revoked:
        record.revoked = True
        db.commit()
    return None


@router.get("/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user

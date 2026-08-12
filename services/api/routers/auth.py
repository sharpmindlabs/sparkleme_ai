"""Authentication endpoints (FR-1)."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import User, UserStatus
from ..schemas import LoginRequest, TokenResponse
from ..security import verify_password, issue_token, current_user
from ..serializers import user_out

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_session)):
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid email or password")
    if user.status == UserStatus.SUSPENDED:
        # FR-1.3: suspended users blocked with support message.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "account suspended — contact support")
    return TokenResponse(
        access_token=issue_token(user), role=user.role.value, name=user.name, user_id=user.id,
    )


@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return user_out(user)

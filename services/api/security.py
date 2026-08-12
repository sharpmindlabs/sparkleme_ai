"""Auth: password hashing (bcrypt), JWT issue/verify, RBAC dependencies.

Sandbox substitution for Keycloak: local email/password -> signed JWT carrying a
role claim. The dependency structure (bearer token -> claims -> role gate) is the
same shape an OIDC/SSO integration would slot into.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_session
from .models import User, Role, UserStatus

_settings = get_settings()
_bearer = HTTPBearer(auto_error=False)


# --------------------------------------------------------------------------- passwords
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- jwt
def issue_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role.value,
        "name": user.name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=_settings.jwt_expiry_minutes)).timestamp()),
    }
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, _settings.jwt_secret, algorithms=[_settings.jwt_algorithm])


# --------------------------------------------------------------------------- deps
def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_session),
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    try:
        claims = decode_token(creds.credentials)
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {e}")
    user = db.get(User, claims.get("sub"))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unknown subject")
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "account suspended — contact support")
    return user


def require_roles(*roles: Role):
    """Dependency factory enforcing the §2 RBAC matrix."""
    allowed = set(roles)

    def _guard(user: User = Depends(current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"role {user.role.value} not permitted (requires one of {[r.value for r in allowed]})",
            )
        return user

    return _guard

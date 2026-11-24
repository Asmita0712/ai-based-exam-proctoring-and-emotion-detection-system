"""
FastAPI authentication and RBAC authorization dependencies.
Enforces strict role boundaries for:
- Public Students (attempt-token validated, no user account)
- Teachers (authenticated, role in ['teacher', 'admin'])
- Administrators (authenticated, role == 'admin')
"""
from typing import Dict, Optional
from fastapi import Cookie, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.models import ExamAttempt, User
from app.db.session import get_db

security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolves the authenticated staff User from Authorization header or HttpOnly cookie.
    Raises 401 if unauthenticated.
    """
    token = None
    if auth and auth.credentials:
        token = auth.credentials
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload or payload.get("type") == "student_attempt":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found or deactivated.")

    return user


def require_teacher(current_user: User = Depends(get_current_user)) -> User:
    """Verifies that the caller has Teacher or Admin privileges."""
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Teacher or Administrator access required.",
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Verifies that the caller has Administrator privileges."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrator access required.",
        )
    return current_user


def get_current_student_attempt(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    x_attempt_token: Optional[str] = Header(None, alias="X-Attempt-Token"),
    db: Session = Depends(get_db),
) -> ExamAttempt:
    """
    Validates a student's active exam attempt token.
    Enforces server-side authoritative timer validity.
    """
    token = x_attempt_token or (auth.credentials if auth else None)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Examination attempt token required.",
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "student_attempt":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired examination attempt token.",
        )

    attempt_id = payload.get("attempt_id")
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examination attempt not found.")

    return attempt

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select

from ..db import get_db
from ..models import Account, Transaction, User

router = APIRouter()
_hasher = PasswordHasher()
_SESSION_SECONDS = 20 * 60


class AdminLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=12, max_length=200)


def _settings():
    username = os.getenv("ADMIN_USERNAME", "").strip()
    password_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip()
    secret = os.getenv("ADMIN_SESSION_SECRET", "").strip()
    if not username or not password_hash or len(secret) < 32:
        raise HTTPException(503, "Administrator login is not configured")
    return username, password_hash, secret


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _issue_token(username: str, secret: str) -> str:
    payload = {"sub": username, "exp": int(time.time()) + _SESSION_SECONDS}
    body = _encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _encode(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"


def require_private_admin(x_admin_token: str | None = Header(default=None)):
    username, _, secret = _settings()
    if not x_admin_token or "." not in x_admin_token:
        raise HTTPException(401, "Administrator login required")
    body, signature = x_admin_token.split(".", 1)
    expected = _encode(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(401, "Invalid administrator session")
    try:
        payload = json.loads(_decode(body))
    except Exception as exc:
        raise HTTPException(401, "Invalid administrator session") from exc
    if payload.get("sub") != username or int(payload.get("exp", 0)) <= int(time.time()):
        raise HTTPException(401, "Administrator session expired")
    return username


def mask_email(value: str) -> str:
    local, separator, domain = (value or "").partition("@")
    if not separator:
        return "hidden"
    visible = local[:2] if len(local) >= 2 else local[:1]
    return f"{visible}{'*' * max(3, len(local) - len(visible))}@{domain}"


@router.post("/admin/login")
def admin_login(data: AdminLogin):
    username, password_hash, secret = _settings()
    username_ok = hmac.compare_digest(data.username.strip().casefold(), username.casefold())
    try:
        password_ok = _hasher.verify(password_hash, data.password)
    except VerifyMismatchError:
        password_ok = False
    except Exception:
        password_ok = False
    if not username_ok or not password_ok:
        time.sleep(0.6)
        raise HTTPException(401, "Invalid administrator credentials")
    return {"token": _issue_token(username, secret), "expires_in_seconds": _SESSION_SECONDS}


@router.get("/admin/overview")
def admin_overview(admin=Depends(require_private_admin), db=Depends(get_db)):
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    recent_users = db.scalars(select(User).order_by(User.created_at.desc()).limit(50)).all()
    return {
        "metrics": {
            "users": db.scalar(select(func.count()).select_from(User)) or 0,
            "transactions": db.scalar(select(func.count()).select_from(Transaction)) or 0,
            "accounts": db.scalar(select(func.count()).select_from(Account)) or 0,
            "registrations_last_7_days": sum(
                1 for user in recent_users
                if getattr(user, "created_at", None) and user.created_at >= seven_days_ago
            ),
        },
        "users": [
            {"id": user.id, "masked_email": mask_email(user.email), "created_at": user.created_at}
            for user in recent_users
        ],
        "privacy": {"financial_records_visible": False, "emails_masked": True},
    }
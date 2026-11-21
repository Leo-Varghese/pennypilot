import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select

from ..db import get_db
from ..models import Account, Transaction, User
from ..security import current_user

router = APIRouter()


def admin_emails() -> set[str]:
    return {
        value.strip().casefold()
        for value in os.getenv("ADMIN_EMAILS", "").split(",")
        if value.strip()
    }


def require_admin(user=Depends(current_user)):
    email = (getattr(user, "email", "") or "").strip().casefold()
    if not email or email not in admin_emails():
        raise HTTPException(403, "Administrator access required")
    return user


def mask_email(value: str) -> str:
    local, separator, domain = (value or "").partition("@")
    if not separator:
        return "hidden"
    visible = local[:2] if len(local) >= 2 else local[:1]
    return f"{visible}{'*' * max(3, len(local) - len(visible))}@{domain}"


@router.get("/admin/overview")
def admin_overview(admin=Depends(require_admin), db=Depends(get_db)):
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    user_count = db.scalar(select(func.count()).select_from(User)) or 0
    transaction_count = db.scalar(select(func.count()).select_from(Transaction)) or 0
    account_count = db.scalar(select(func.count()).select_from(Account)) or 0

    recent_users = db.scalars(
        select(User).order_by(User.created_at.desc()).limit(50)
    ).all()
    registrations_last_7_days = sum(
        1 for user in recent_users
        if getattr(user, "created_at", None)
        and user.created_at >= seven_days_ago
    )

    return {
        "metrics": {
            "users": user_count,
            "transactions": transaction_count,
            "accounts": account_count,
            "registrations_last_7_days": registrations_last_7_days,
        },
        "users": [
            {
                "id": user.id,
                "masked_email": mask_email(user.email),
                "created_at": getattr(user, "created_at", None),
            }
            for user in recent_users
        ],
        "privacy": {
            "financial_records_visible": False,
            "emails_masked": True,
            "admin_source": "ADMIN_EMAILS server environment variable",
        },
    }


@router.get("/admin/me")
def admin_me(admin=Depends(require_admin)):
    return {"is_admin": True, "email": mask_email(admin.email)}
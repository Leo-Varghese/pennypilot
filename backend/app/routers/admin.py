import asyncio
import base64
import hashlib
import hmac
import json
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text

from ..db import get_db
from ..models import Account, Transaction, User

router = APIRouter()
_hasher = PasswordHasher()
_SESSION_SECONDS = 20 * 60
_DOCTOR_INTERVAL_SECONDS = 6 * 60 * 60
_doctor_cache: dict[str, Any] = {"checked_at": None, "checks": [], "summary": {"healthy": 0, "warnings": 0, "failures": 0}}
_doctor_lock = asyncio.Lock()
_doctor_task: asyncio.Task | None = None


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


def _result(name: str, status: str, detail: str, recommendation: str = "", caveat: str = ""):
    return {"name": name, "status": status, "detail": detail, "recommendation": recommendation, "caveat": caveat}


async def _run_site_doctor() -> dict[str, Any]:
    global _doctor_cache
    async with _doctor_lock:
        checks: list[dict[str, str]] = []
        frontend = os.getenv("FRONTEND_ORIGIN", os.getenv("FRONTEND_ORIGINS", "https://pennypilot-swart.vercel.app")).split(",")[0].strip().rstrip("/")

        try:
            started = time.perf_counter()
            async with httpx.AsyncClient(timeout=httpx.Timeout(75.0)) as client:
                response = await client.get(frontend + "/", headers={"User-Agent": "PennyPilot-Site-Doctor/1.0"})
            elapsed = round(time.perf_counter() - started, 2)
            if response.status_code == 200 and "Welcome back" in response.text:
                status = "warning" if elapsed >= 30 else "healthy"
                checks.append(_result(
                    "Public website",
                    status,
                    f"HTTP 200 in {elapsed} seconds.",
                    "Consider always-on hosting only when cold starts materially affect users." if status == "warning" else "No action required.",
                    "Free-tier services can need 30 to 40 seconds to wake." if status == "warning" else "",
                ))
            else:
                checks.append(_result("Public website", "failure", f"HTTP {response.status_code}; expected login-page text was not found.", "Check the latest Vercel deployment and frontend logs."))
        except Exception as exc:
            checks.append(_result("Public website", "failure", f"Request failed: {type(exc).__name__}.", "Check Vercel deployment status, DNS, and the configured frontend origin."))

        try:
            status, body = await _database_probe()
            checks.append(_result("Database readiness", status, body, "Check DATABASE_URL, Neon status, connection limits, and pending migrations." if status == "failure" else "No action required."))
        except Exception as exc:
            checks.append(_result("Database readiness", "failure", f"Probe failed: {type(exc).__name__}.", "Check DATABASE_URL, Neon status, and Render logs."))

        try:
            completed = subprocess.run(["python", "-m", "alembic", "heads"], capture_output=True, text=True, timeout=20, check=False)
            heads = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
            if completed.returncode == 0 and len(heads) == 1:
                checks.append(_result("Migration chain", "healthy", f"One Alembic head detected: {heads[0]}", "No action required."))
            else:
                detail = completed.stderr.strip()[:300] or f"Expected one head; detected {len(heads)}."
                checks.append(_result("Migration chain", "failure", detail, "Resolve migration errors or multiple heads before the next deployment."))
        except Exception as exc:
            checks.append(_result("Migration chain", "failure", f"Check failed: {type(exc).__name__}.", "Run python -m alembic heads locally and inspect migration files."))

        ai_key = bool(os.getenv("GROQ_API_KEY", "").strip())
        ai_model = bool(os.getenv("GROQ_MODEL", "").strip())
        checks.append(_result(
            "AI configuration",
            "healthy" if ai_key and ai_model else "warning",
            "Groq key and model are configured." if ai_key and ai_model else "Groq key or model is missing.",
            "No action required." if ai_key and ai_model else "Set GROQ_API_KEY and GROQ_MODEL only in the Render backend environment.",
            "This check verifies configuration only; it never displays or sends the secret.",
        ))

        admin_configured = bool(os.getenv("ADMIN_USERNAME", "").strip() and os.getenv("ADMIN_PASSWORD_HASH", "").startswith("$argon2") and len(os.getenv("ADMIN_SESSION_SECRET", "")) >= 32)
        checks.append(_result(
            "Private admin configuration",
            "healthy" if admin_configured else "failure",
            "Separate admin credentials and session signing are configured." if admin_configured else "One or more private admin variables are invalid.",
            "No action required." if admin_configured else "Check ADMIN_USERNAME, the complete Argon2 ADMIN_PASSWORD_HASH, and ADMIN_SESSION_SECRET in Render.",
        ))

        counts = {
            "healthy": sum(item["status"] == "healthy" for item in checks),
            "warnings": sum(item["status"] == "warning" for item in checks),
            "failures": sum(item["status"] == "failure" for item in checks),
        }
        _doctor_cache = {"checked_at": datetime.now(timezone.utc).isoformat(), "checks": checks, "summary": counts}
        return _doctor_cache


async def _database_probe() -> tuple[str, str]:
    from ..db import SessionLocal
    try:
        with SessionLocal() as db:
            value = db.scalar(text("SELECT 1"))
            if value == 1:
                return "healthy", "Database connection and basic query succeeded."
            return "failure", "Database returned an unexpected readiness value."
    except Exception:
        return "failure", "Database connection or basic query failed."


async def _doctor_loop():
    await asyncio.sleep(20)
    while True:
        try:
            await _run_site_doctor()
        except Exception:
            pass
        await asyncio.sleep(_DOCTOR_INTERVAL_SECONDS)


@router.on_event("startup")
async def start_site_doctor():
    global _doctor_task
    if _doctor_task is None or _doctor_task.done():
        _doctor_task = asyncio.create_task(_doctor_loop())


@router.post("/admin/login")
def admin_login(data: AdminLogin):
    username, password_hash, secret = _settings()
    username_ok = hmac.compare_digest(data.username.strip().casefold(), username.casefold())
    try:
        password_ok = _hasher.verify(password_hash, data.password)
    except (VerifyMismatchError, Exception):
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
            "registrations_last_7_days": sum(1 for user in recent_users if getattr(user, "created_at", None) and user.created_at >= seven_days_ago),
        },
        "users": [{"id": user.id, "masked_email": mask_email(user.email), "created_at": user.created_at} for user in recent_users],
    }


@router.get("/admin/site-doctor")
async def site_doctor_report(admin=Depends(require_private_admin)):
    if not _doctor_cache["checked_at"]:
        return await _run_site_doctor()
    return _doctor_cache


@router.post("/admin/site-doctor/run")
async def run_site_doctor(admin=Depends(require_private_admin)):
    return await _run_site_doctor()
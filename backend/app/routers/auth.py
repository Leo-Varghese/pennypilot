from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, delete, update
from ..db import get_db
from ..models import *
from ..schemas import Credentials, PreferenceIn
from ..security import current_user, passwords, DUMMY_HASH, throttle, issue_session, digest
from ..serialization import serialize
router=APIRouter()

@router.post("/auth/register",status_code=201)
def register(data:Credentials,request:Request,db=Depends(get_db)):
    email=str(data.email).lower()
    throttle(db,"register:"+(request.client.host if request.client else "unknown"))
    if db.scalar(select(User).where(User.email==email)): raise HTTPException(409,"Unable to register this email")
    user=User(email=email,password_hash=passwords.hash(data.password)); db.add(user); db.flush()
    db.add(Preference(user_id=user.id))
    for name in ["Food & groceries","Transport","Housing","Utilities","Shopping","Health","Education","Entertainment","Salary","Other"]: db.add(Category(user_id=user.id,name=name))
    return issue_session(db,user)

@router.post("/auth/login")
def login(data:Credentials,request:Request,db=Depends(get_db)):
    email=str(data.email).lower(); throttle(db,"login-email:"+email)
    throttle(db,"login-ip:"+(request.client.host if request.client else "unknown"))
    user=db.scalar(select(User).where(User.email==email))
    valid=passwords.verify(data.password,user.password_hash if user else DUMMY_HASH)
    if not user or not valid: raise HTTPException(401,"Invalid email or password")
    return issue_session(db,user)

@router.post("/auth/logout",status_code=204)
def logout(request:Request,user=Depends(current_user),db=Depends(get_db)):
    db.execute(delete(Session).where(Session.token_hash==digest(request.headers.get("authorization","").split()[-1]),Session.user_id==user.id)); db.commit()

@router.get("/auth/me")
def me(user=Depends(current_user)): return {"id":user.id,"email":user.email}

@router.get("/preferences")
def preferences(user=Depends(current_user),db=Depends(get_db)): return {k:v for k,v in serialize(db.get(Preference,user.id)).items() if k != "user_id"}

@router.put("/preferences")
def update_preferences(data:PreferenceIn,user=Depends(current_user),db=Depends(get_db)):
    row=db.get(Preference,user.id)
    for k,v in data.model_dump().items(): setattr(row,k,v)
    db.commit(); return serialize(row)

@router.delete("/auth/me",status_code=204)
def delete_me(data:Credentials,user=Depends(current_user),db=Depends(get_db)):
    if str(data.email).lower()!=user.email or not passwords.verify(data.password,user.password_hash): raise HTTPException(403,"Confirm credentials")
    db.execute(delete(BillPayment).where(BillPayment.recurring_id.in_(select(Recurring.id).where(Recurring.user_id==user.id))))
    db.execute(delete(Receipt).where(Receipt.user_id==user.id))
    db.execute(delete(TransactionTag).where(TransactionTag.transaction_id.in_(select(Transaction.id).where(Transaction.user_id==user.id))))
    db.execute(delete(Transaction).where(Transaction.user_id==user.id))
    db.execute(delete(Recurring).where(Recurring.user_id==user.id))
    db.execute(delete(Allocation).where(Allocation.budget_id.in_(select(Budget.id).where(Budget.user_id==user.id))))
    db.execute(update(Budget).where(Budget.user_id==user.id).values(previous_id=None))
    db.execute(delete(Budget).where(Budget.user_id==user.id))
    db.execute(update(Category).where(Category.user_id==user.id).values(parent_id=None))
    db.delete(user); db.commit()

# Password recovery uses a neutral response to avoid revealing registered emails.
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
import httpx
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class ForgotPasswordIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr

class ResetPasswordIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=32, max_length=300)
    password: str = Field(min_length=12, max_length=128)


def reset_digest(value: str) -> str:
    secret = os.getenv("PASSWORD_RESET_SECRET", "").strip()
    if len(secret) < 32:
        raise HTTPException(503, "Password reset is temporarily unavailable")
    return hashlib.sha256((secret + value).encode()).hexdigest()


def send_reset_email(recipient: str, link: str):
    key = os.getenv("BREVO_API_KEY", "").strip()
    sender_value = os.getenv("EMAIL_FROM", "").strip()
    if not key or not sender_value:
        raise RuntimeError("Email delivery is not configured")
    if "<" in sender_value and sender_value.endswith(">"):
        sender_name, sender_email = sender_value.rsplit("<", 1)
        sender = {"name": sender_name.strip(), "email": sender_email[:-1].strip()}
    else:
        sender = {"name": "PennyPilot", "email": sender_value}
    payload = {
        "sender": sender,
        "to": [{"email": recipient}],
        "subject": "Reset your PennyPilot password",
        "htmlContent": f"""<p>A password reset was requested for your PennyPilot account.</p>
<p><a href=\"{link}\">Reset your password</a></p>
<p>This link expires in 30 minutes and can be used once.</p>
<p>If you did not request this, you can ignore this email.</p>""",
    }
    response = httpx.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": key, "Content-Type": "application/json", "Accept": "application/json"},
        json=payload,
        timeout=20.0,
    )
    response.raise_for_status()


@router.post("/auth/forgot-password")
def forgot_password(data: ForgotPasswordIn, request: Request, db=Depends(get_db)):
    email = str(data.email).strip().lower()
    throttle(db, "forgot-email:" + email)
    throttle(db, "forgot-ip:" + (request.client.host if request.client else "unknown"))
    user = db.scalar(select(User).where(User.email == email))
    message = "If an account exists for that email, PennyPilot has sent password-reset instructions."
    if not user:
        return {"message": message}

    now = datetime.now(timezone.utc)
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
    raw_token = secrets.token_urlsafe(48)
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=reset_digest(raw_token),
        expires_at=now + timedelta(minutes=30),
    ))
    db.commit()

    frontend = os.getenv("FRONTEND_ORIGIN", "").strip() or os.getenv("FRONTEND_ORIGINS", "").split(",")[0].strip()
    if not frontend:
        raise HTTPException(503, "Password reset is temporarily unavailable")
    try:
        send_reset_email(email, frontend.rstrip("/") + "/reset-password?token=" + raw_token)
    except Exception:
        # Do not expose provider or account details to the requester.
        raise HTTPException(503, "Password reset email could not be sent. Please try again later.")
    return {"message": message}


@router.post("/auth/reset-password")
def reset_password(data: ResetPasswordIn, request: Request, db=Depends(get_db)):
    throttle(db, "reset-ip:" + (request.client.host if request.client else "unknown"))
    now = datetime.now(timezone.utc)
    row = db.scalar(select(PasswordResetToken).where(
        PasswordResetToken.token_hash == reset_digest(data.token),
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > now,
    ))
    if not row:
        raise HTTPException(400, "This password-reset link is invalid or expired")
    user = db.get(User, row.user_id)
    if not user:
        raise HTTPException(400, "This password-reset link is invalid or expired")
    user.password_hash = passwords.hash(data.password)
    row.used_at = now
    db.execute(delete(Session).where(Session.user_id == user.id))
    db.commit()
    return {"message": "Password updated. Sign in with your new password."}
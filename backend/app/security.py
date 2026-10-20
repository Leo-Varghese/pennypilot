import hashlib, hmac, secrets
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pwdlib import PasswordHash
from sqlalchemy import select
from .db import get_db
from .config import settings
from .models import User, Session, AuthAttempt

passwords = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
DUMMY_HASH = passwords.hash("not-a-real-password-123456")

def digest(value):
    return hmac.new(settings.session_secret.encode(), value.encode(), hashlib.sha256).hexdigest()

def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db=Depends(get_db)):
    if not credentials: raise HTTPException(401, "Sign in required")
    session = db.get(Session, digest(credentials.credentials))
    if not session or utc(session.expires_at) <= datetime.now(timezone.utc): raise HTTPException(401, "Session expired")
    user = db.get(User, session.user_id)
    if not user: raise HTTPException(401, "Session expired")
    return user

def issue_session(db, user):
    token = secrets.token_urlsafe(48)
    db.add(Session(token_hash=digest(token), user_id=user.id, expires_at=datetime.now(timezone.utc)+timedelta(hours=settings.session_hours)))
    db.commit()
    return {"access_token": token, "token_type": "bearer", "expires_in": settings.session_hours*3600}

def throttle(db, key):
    key = digest(key)
    now = datetime.now(timezone.utc)
    row = db.scalar(select(AuthAttempt).where(AuthAttempt.key == key).with_for_update())
    if row is None:
        row = AuthAttempt(key=key, count=0, window=now); db.add(row)
    if now - utc(row.window) > timedelta(minutes=15): row.count=0; row.window=now
    if row.count >= 10: raise HTTPException(429, "Too many attempts. Try again after the 15-minute window.")
    row.count += 1
    db.commit()

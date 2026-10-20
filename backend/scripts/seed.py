"""Explicit, synthetic development fixture. Never runs during deploy."""
import argparse
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import select
from app.config import settings
from app.db import SessionLocal
from app.models import User, Preference, Account, Category
from app.security import passwords
from app.schemas import TransactionIn
from app.services.ledger import save_transaction

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--confirm-synthetic",action="store_true",required=True)
    parser.add_argument("--email",default="demo@example.com")
    args=parser.parse_args()
    if settings.app_env != "development": raise SystemExit("Seed is restricted to APP_ENV=development")
    import getpass
    password=getpass.getpass("Choose a demo password (12+ characters): ")
    if len(password)<12: raise SystemExit("Password too short")
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email==args.email)): raise SystemExit("Demo user already exists; no data changed")
        user=User(email=args.email,password_hash=passwords.hash(password));db.add(user);db.flush()
        db.add(Preference(user_id=user.id));db.flush()
        account=Account(user_id=user.id,name="SYNTHETIC DEMO Bank",type="savings",currency="INR",opening_balance=Decimal("1000"),opening_date=date(2025,1,1));db.add(account)
        category=Category(user_id=user.id,name="SYNTHETIC DEMO Food");db.add(category);db.flush()
        for kind,amount,merchant in [("income","25000.00","SYNTHETIC DEMO Income"),("expense","1250.00","SYNTHETIC DEMO Groceries")]:
            save_transaction(db,TransactionIn(kind=kind,amount=amount,currency="INR",occurred_at=datetime.now(timezone.utc),account_id=account.id,category_id=category.id,merchant=merchant,notes="Synthetic development fixture, not genuine financial history"),user.id)
        db.commit()
    print("Synthetic demo user created. Sign in using your chosen credentials.")
if __name__=="__main__": main()

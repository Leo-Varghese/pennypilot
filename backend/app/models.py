from datetime import datetime, timezone, date
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import String, ForeignKey, Numeric, Date, DateTime, Integer, Boolean, Text, LargeBinary, CheckConstraint, UniqueConstraint, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Preference(Base):
    __tablename__ = "preferences"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata")
    zero_based: Mapped[bool] = mapped_column(Boolean, default=False)

class Session(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class AuthAttempt(Base):
    __tablename__ = "auth_attempts"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    window: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Owned:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

class Account(Owned, Base):
    __tablename__ = "accounts"
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(30))
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    opening_date: Mapped[date] = mapped_column(Date, default=date.today)

class Category(Owned, Base):
    __tablename__ = "categories"
    name: Mapped[str] = mapped_column(String(80))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    __table_args__ = (UniqueConstraint("user_id", "name"),)

class Tag(Owned, Base):
    __tablename__ = "tags"
    name: Mapped[str] = mapped_column(String(50))
    __table_args__ = (UniqueConstraint("user_id", "name"),)

class Transaction(Owned, Base):
    __tablename__ = "transactions"
    kind: Mapped[str] = mapped_column(String(20))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[str] = mapped_column(String(3))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), index=True)
    destination_id: Mapped[str | None] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), index=True)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
    merchant: Mapped[str] = mapped_column(String(160), default="")
    payment_method: Mapped[str] = mapped_column(String(30), default="upi")
    location: Mapped[str] = mapped_column(String(200), default="")
    purpose: Mapped[str] = mapped_column(String(300), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    adjustment_direction: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    __table_args__ = (
        CheckConstraint("amount > 0", name="positive_transaction_amount"),
        CheckConstraint("kind IN ('income','expense','transfer','refund','adjustment')", name="valid_transaction_kind"),
        CheckConstraint("adjustment_direction IN (-1,1)", name="valid_adjustment_direction"),
        CheckConstraint("(kind = 'transfer' AND destination_id IS NOT NULL AND destination_id <> account_id) OR (kind <> 'transfer' AND destination_id IS NULL)", name="transfer_destination"),
        Index("ix_transaction_owner_date", "user_id", "occurred_at"),
    )

class TransactionTag(Base):
    __tablename__ = "transaction_tags"
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[str] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

class Receipt(Owned, Base):
    __tablename__ = "receipts"
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"), unique=True)
    content_type: Mapped[str] = mapped_column(String(30))
    data: Mapped[bytes] = mapped_column(LargeBinary)

class Budget(Owned, Base):
    __tablename__ = "budgets"
    name: Mapped[str] = mapped_column(String(100))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    rollover: Mapped[bool] = mapped_column(Boolean, default=False)
    previous_id: Mapped[str | None] = mapped_column(ForeignKey("budgets.id", ondelete="RESTRICT"))
    __table_args__ = (CheckConstraint("end_date >= start_date", name="budget_dates"),)

class Allocation(Base):
    __tablename__ = "allocations"
    budget_id: Mapped[str] = mapped_column(ForeignKey("budgets.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    __table_args__ = (CheckConstraint("amount >= 0", name="positive_allocation"),)

class Goal(Owned, Base):
    __tablename__ = "goals"
    name: Mapped[str] = mapped_column(String(100))
    target_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    target_date: Mapped[date | None] = mapped_column(Date)
    priority: Mapped[int] = mapped_column(Integer, default=2)
    __table_args__ = (CheckConstraint("target_amount > 0", name="positive_goal"),)

class Contribution(Owned, Base):
    __tablename__ = "contributions"
    goal_id: Mapped[str] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    date: Mapped[date] = mapped_column(Date)
    note: Mapped[str] = mapped_column(String(300), default="")
    __table_args__ = (CheckConstraint("amount > 0", name="positive_contribution"),)

class Recurring(Owned, Base):
    __tablename__ = "recurring"
    name: Mapped[str] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(20))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"))
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    next_due: Mapped[date] = mapped_column(Date)
    frequency: Mapped[str] = mapped_column(String(20), default="monthly")
    anchor_day: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (CheckConstraint("amount > 0", name="positive_recurring"),)

class BillPayment(Base):
    __tablename__ = "bill_payments"
    recurring_id: Mapped[str] = mapped_column(ForeignKey("recurring.id", ondelete="CASCADE"), primary_key=True)
    due_date: Mapped[date] = mapped_column(Date, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.id", ondelete="RESTRICT"), unique=True)

class Holding(Owned, Base):
    __tablename__ = "holdings"
    name: Mapped[str] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(20))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    valued_on: Mapped[date] = mapped_column(Date)
    __table_args__ = (CheckConstraint("amount >= 0", name="positive_holding"), CheckConstraint("kind IN ('asset','liability')", name="holding_kind"))

class Snapshot(Owned, Base):
    __tablename__ = "snapshots"
    date: Mapped[date] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3))
    assets: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    liabilities: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    __table_args__ = (UniqueConstraint("user_id", "date", "currency"),)

class ImportBatch(Owned, Base):
    __tablename__ = "import_batches"
    digest: Mapped[str] = mapped_column(String(64))
    count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint("user_id", "digest"),)

from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from ..db import get_db
from ..models import Account, Category, PlannedPurchase, Preference
from ..schemas import TransactionIn
from ..security import current_user
from ..serialization import serialize
from ..services.ledger import owned, save_transaction

router = APIRouter()


class PlannedPurchaseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    planned_amount: Decimal = Field(gt=0, max_digits=20, decimal_places=2)
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")
    category_id: str | None = None
    merchant: str = Field(default="", max_length=160)
    priority: int = Field(default=2, ge=1, le=3)
    target_date: date | None = None
    notes: str = Field(default="", max_length=2000)


class PurchaseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_id: str
    purchased_on: date
    payment_method: str = Field(pattern=r"^(upi|cash|debit_card|credit_card|wallet|bank_transfer|other)$")
    actual_amount: Decimal | None = Field(default=None, gt=0, max_digits=20, decimal_places=2)


def validate_related(db, data: PlannedPurchaseIn, user_id: str):
    if data.category_id:
        owned(db, Category, data.category_id, user_id)


@router.get("/planned-purchases")
def list_planned_purchases(
    status: str = Query("planned", pattern=r"^(planned|purchased|cancelled|all)$"),
    currency: str | None = None,
    user=Depends(current_user),
    db=Depends(get_db),
):
    stmt = select(PlannedPurchase).where(PlannedPurchase.user_id == user.id)
    if status != "all":
        stmt = stmt.where(PlannedPurchase.status == status)
    if currency:
        stmt = stmt.where(PlannedPurchase.currency == currency)
    rows = db.scalars(
        stmt.order_by(
            PlannedPurchase.priority.asc(),
            PlannedPurchase.target_date.asc().nullslast(),
            PlannedPurchase.created_at.desc(),
        )
    ).all()
    return serialize(rows)


@router.post("/planned-purchases", status_code=201)
def create_planned_purchase(data: PlannedPurchaseIn, user=Depends(current_user), db=Depends(get_db)):
    validate_related(db, data, user.id)
    row = PlannedPurchase(user_id=user.id, **data.model_dump())
    db.add(row)
    db.commit()
    return serialize(row)


@router.put("/planned-purchases/{purchase_id}")
def update_planned_purchase(purchase_id: str, data: PlannedPurchaseIn, user=Depends(current_user), db=Depends(get_db)):
    row = owned(db, PlannedPurchase, purchase_id, user.id, True)
    if row.status != "planned":
        raise HTTPException(409, "Only planned items can be edited")
    validate_related(db, data, user.id)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return serialize(row)


@router.delete("/planned-purchases/{purchase_id}", status_code=204)
def delete_planned_purchase(purchase_id: str, user=Depends(current_user), db=Depends(get_db)):
    row = owned(db, PlannedPurchase, purchase_id, user.id)
    if row.status == "purchased":
        raise HTTPException(409, "Purchased items are linked to transactions and cannot be deleted here")
    db.delete(row)
    db.commit()


@router.post("/planned-purchases/{purchase_id}/cancel")
def cancel_planned_purchase(purchase_id: str, user=Depends(current_user), db=Depends(get_db)):
    row = owned(db, PlannedPurchase, purchase_id, user.id, True)
    if row.status != "planned":
        raise HTTPException(409, "Only planned items can be cancelled")
    row.status = "cancelled"
    db.commit()
    return serialize(row)


@router.post("/planned-purchases/{purchase_id}/purchase")
def purchase_planned_item(purchase_id: str, data: PurchaseIn, user=Depends(current_user), db=Depends(get_db)):
    row = owned(db, PlannedPurchase, purchase_id, user.id, True)
    if row.status != "planned":
        raise HTTPException(409, "This planned purchase has already been completed or cancelled")

    account = owned(db, Account, data.account_id, user.id, True)
    if account.currency != row.currency:
        raise HTTPException(422, "Account currency must match the planned purchase currency")

    preferences = db.get(Preference, user.id)
    zone = ZoneInfo(preferences.timezone)
    amount = data.actual_amount or row.planned_amount

    transaction = save_transaction(
        db,
        TransactionIn(
            kind="expense",
            amount=amount,
            currency=row.currency,
            occurred_at=datetime.combine(data.purchased_on, time(12), zone),
            account_id=account.id,
            category_id=row.category_id,
            merchant=row.merchant or row.name,
            payment_method=data.payment_method,
            purpose=f"Planned purchase: {row.name}",
            notes=row.notes,
        ),
        user.id,
    )
    row.status = "purchased"
    row.transaction_id = transaction.id
    db.commit()
    return {"planned_purchase": serialize(row), "transaction": serialize(transaction)}
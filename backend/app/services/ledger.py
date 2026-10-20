from datetime import datetime, date, time, timezone, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
from sqlalchemy import select, func, case, or_
from fastapi import HTTPException
from ..models import Account, Category, Transaction, Tag, TransactionTag, Preference

ZERO = Decimal("0.00")

def owned(db, model, id, user_id, lock=False):
    stmt = select(model).where(model.id == id, model.user_id == user_id)
    if lock: stmt = stmt.with_for_update()
    obj = db.scalar(stmt)
    if obj is None: raise HTTPException(404, "Record not found")
    return obj

def bounds(start, end, zone):
    if end < start: raise HTTPException(422, "Invalid date range")
    tz = ZoneInfo(zone)
    return datetime.combine(start,time.min,tz).astimezone(timezone.utc), datetime.combine(end+timedelta(days=1),time.min,tz).astimezone(timezone.utc)

def base_query(user_id, currency, start=None, end=None, zone="Asia/Kolkata"):
    stmt = select(Transaction).where(Transaction.user_id == user_id, Transaction.currency == currency)
    if start is not None and end is not None:
        a,b = bounds(start,end,zone); stmt = stmt.where(Transaction.occurred_at >= a, Transaction.occurred_at < b)
    return stmt

def validate_transaction(db, data, user_id):
    account = owned(db, Account, data.account_id, user_id)
    if account.currency != data.currency: raise HTTPException(422, "Currency must match account; FX transfers are not supported")
    local_date = data.occurred_at.astimezone(ZoneInfo(db.get(Preference,user_id).timezone)).date()
    if local_date < account.opening_date: raise HTTPException(422, "Transaction precedes account opening date")
    if data.destination_id:
        destination = owned(db, Account, data.destination_id, user_id)
        if destination.currency != data.currency: raise HTTPException(422, "Cross-currency transfer requires FX support, not available")
        if local_date < destination.opening_date: raise HTTPException(422, "Transfer precedes destination opening date")
    if data.category_id: owned(db, Category, data.category_id, user_id)

def save_transaction(db, data, user_id, existing=None):
    validate_transaction(db,data,user_id)
    tx = existing or Transaction(user_id=user_id)
    for key,value in data.model_dump(exclude={"tags"}).items(): setattr(tx,key,value)
    db.add(tx); db.flush()
    db.query(TransactionTag).filter(TransactionTag.transaction_id == tx.id).delete()
    for name in sorted(set(data.tags)):
        tag = db.scalar(select(Tag).where(Tag.user_id == user_id, Tag.name == name))
        if tag is None: tag=Tag(user_id=user_id,name=name); db.add(tag); db.flush()
        db.add(TransactionTag(transaction_id=tx.id,tag_id=tag.id))
    return tx

def totals(db, stmt):
    sub=stmt.subquery()
    income=func.coalesce(func.sum(case((sub.c.kind == "income",sub.c.amount),else_=0)),0)
    expenses=func.coalesce(func.sum(case((sub.c.kind == "expense",sub.c.amount),(sub.c.kind == "refund",-sub.c.amount),else_=0)),0)
    i,e=db.execute(select(income,expenses)).one()
    i,e=Decimal(i),Decimal(e)
    return {"income":i,"expenses":e,"cash_flow":i-e,"actual_savings":i-e,"savings_rate":((i-e)/i*100).quantize(Decimal("0.01")) if i>0 else None}

def balances(db,user_id,currency,as_of=None):
    accounts=db.scalars(select(Account).where(Account.user_id == user_id,Account.currency == currency)).all()
    stmt=select(Transaction).where(Transaction.user_id == user_id,Transaction.currency == currency)
    if as_of: stmt=stmt.where(Transaction.occurred_at < as_of)
    sub=stmt.subquery()
    sign=case((sub.c.kind.in_(["income","refund"]),sub.c.amount),(sub.c.kind == "adjustment",sub.c.amount*sub.c.adjustment_direction),else_=-sub.c.amount)
    outgoing=dict(db.execute(select(sub.c.account_id,func.sum(sign)).group_by(sub.c.account_id)).all())
    incoming=dict(db.execute(select(sub.c.destination_id,func.sum(sub.c.amount)).where(sub.c.kind == "transfer").group_by(sub.c.destination_id)).all())
    return [{"id":a.id,"name":a.name,"type":a.type,"currency":a.currency,"opening_balance":a.opening_balance,"opening_date":a.opening_date,"balance":a.opening_balance+outgoing.get(a.id,ZERO)+incoming.get(a.id,ZERO)} for a in accounts if not as_of or a.opening_date < as_of.date()]

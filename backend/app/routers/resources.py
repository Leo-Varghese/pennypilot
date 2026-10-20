from datetime import date, datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, delete
from ..db import get_db
from ..models import *
from ..schemas import *
from ..security import current_user
from ..serialization import serialize
from ..services.ledger import owned, balances, save_transaction
from ..services.planning import budget_view, goal_view, net_worth
router=APIRouter()

@router.get("/accounts")
def accounts(currency:str|None=None,user=Depends(current_user),db=Depends(get_db)):
    return serialize(balances(db,user.id,currency or db.get(Preference,user.id).currency))

@router.post("/accounts",status_code=201)
def add_account(data:AccountIn,user=Depends(current_user),db=Depends(get_db)):
    row=Account(user_id=user.id,**data.model_dump()); db.add(row); db.commit(); return serialize(row)

@router.put("/accounts/{id}")
def edit_account(id:str,data:AccountIn,user=Depends(current_user),db=Depends(get_db)):
    row=owned(db,Account,id,user.id)
    has_tx=db.scalar(select(Transaction.id).where(Transaction.user_id==user.id,((Transaction.account_id==id)|(Transaction.destination_id==id))).limit(1))
    if has_tx and (data.currency!=row.currency or data.opening_balance!=row.opening_balance or data.opening_date!=row.opening_date): raise HTTPException(409,"Opening fields are locked after transactions; use an adjustment")
    for k,v in data.model_dump().items(): setattr(row,k,v)
    db.commit(); return serialize(row)

@router.delete("/accounts/{id}",status_code=204)
def delete_account(id:str,user=Depends(current_user),db=Depends(get_db)):
    db.delete(owned(db,Account,id,user.id)); db.commit()

@router.get("/categories")
def categories(user=Depends(current_user),db=Depends(get_db)):
    return serialize(db.scalars(select(Category).where(Category.user_id==user.id).order_by(Category.name)).all())

def category_parent(db,data,user_id,id=None):
    if data.parent_id:
        parent=owned(db,Category,data.parent_id,user_id)
        if parent.parent_id or parent.id==id: raise HTTPException(422,"Only two category levels are supported")
        if id and db.scalar(select(Category.id).where(Category.parent_id==id)): raise HTTPException(422,"A parent category cannot become a subcategory")

@router.post("/categories",status_code=201)
def add_category(data:CategoryIn,user=Depends(current_user),db=Depends(get_db)):
    category_parent(db,data,user.id)
    row=Category(user_id=user.id,**data.model_dump()); db.add(row); db.commit(); return serialize(row)

@router.put("/categories/{id}")
def edit_category(id:str,data:CategoryIn,user=Depends(current_user),db=Depends(get_db)):
    row=owned(db,Category,id,user.id); category_parent(db,data,user.id,id)
    row.name=data.name; row.parent_id=data.parent_id; db.commit(); return serialize(row)

@router.delete("/categories/{id}",status_code=204)
def delete_category(id:str,user=Depends(current_user),db=Depends(get_db)):
    db.delete(owned(db,Category,id,user.id)); db.commit()

@router.get("/tags")
def tags(user=Depends(current_user),db=Depends(get_db)): return serialize(db.scalars(select(Tag).where(Tag.user_id==user.id)).all())

@router.get("/budgets")
def budgets(user=Depends(current_user),db=Depends(get_db)):
    zone=db.get(Preference,user.id).timezone
    return serialize([budget_view(db,b,zone) for b in db.scalars(select(Budget).where(Budget.user_id==user.id).order_by(Budget.start_date.desc()))])

def write_budget(db,data,user_id,row=None):
    if data.previous_id:
        prior=owned(db,Budget,data.previous_id,user_id)
        if prior.end_date>=data.start_date or prior.currency!=data.currency: raise HTTPException(422,"Previous budget must end before this period and use same currency")
    for a in data.allocations: owned(db,Category,a.category_id,user_id)
    ids={a.category_id for a in data.allocations}
    for a in data.allocations:
        cat=db.get(Category,a.category_id)
        if cat.parent_id in ids: raise HTTPException(422,"Do not allocate to both parent and subcategory")
    row=row or Budget(user_id=user_id)
    for k,v in data.model_dump(exclude={"allocations"}).items(): setattr(row,k,v)
    db.add(row); db.flush()
    db.execute(delete(Allocation).where(Allocation.budget_id==row.id))
    for a in data.allocations: db.add(Allocation(budget_id=row.id,**a.model_dump()))
    db.commit(); return serialize(budget_view(db,row,db.get(Preference,user_id).timezone))

@router.post("/budgets",status_code=201)
def add_budget(data:BudgetIn,user=Depends(current_user),db=Depends(get_db)): return write_budget(db,data,user.id)

@router.put("/budgets/{id}")
def edit_budget(id:str,data:BudgetIn,user=Depends(current_user),db=Depends(get_db)):
    row=owned(db,Budget,id,user.id)
    if db.scalar(select(Budget.id).where(Budget.previous_id==id)): raise HTTPException(409,"Budget has rollover successors; keep history immutable")
    return write_budget(db,data,user.id,row)

@router.delete("/budgets/{id}",status_code=204)
def delete_budget(id:str,user=Depends(current_user),db=Depends(get_db)):
    db.delete(owned(db,Budget,id,user.id)); db.commit()

@router.get("/goals")
def goals(user=Depends(current_user),db=Depends(get_db)):
    return serialize([goal_view(db,g) for g in db.scalars(select(Goal).where(Goal.user_id==user.id).order_by(Goal.priority))])

@router.post("/goals",status_code=201)
def add_goal(data:GoalIn,user=Depends(current_user),db=Depends(get_db)):
    row=Goal(user_id=user.id,**data.model_dump()); db.add(row); db.commit(); return serialize(goal_view(db,row))

@router.put("/goals/{id}")
def edit_goal(id:str,data:GoalIn,user=Depends(current_user),db=Depends(get_db)):
    row=owned(db,Goal,id,user.id)
    if row.currency!=data.currency and db.scalar(select(Contribution.id).where(Contribution.goal_id==id)): raise HTTPException(409,"Currency locked after contributions")
    for k,v in data.model_dump().items(): setattr(row,k,v)
    db.commit(); return serialize(goal_view(db,row))

@router.delete("/goals/{id}",status_code=204)
def delete_goal(id:str,user=Depends(current_user),db=Depends(get_db)):
    db.delete(owned(db,Goal,id,user.id)); db.commit()

@router.post("/goals/{id}/contributions",status_code=201)
def contribute(id:str,data:ContributionIn,user=Depends(current_user),db=Depends(get_db)):
    goal=owned(db,Goal,id,user.id)
    if data.date>date.today(): raise HTTPException(422,"Future contributions are not actual savings")
    db.add(Contribution(user_id=user.id,goal_id=id,**data.model_dump())); db.commit(); return serialize(goal_view(db,goal))

@router.delete("/contributions/{id}",status_code=204)
def delete_contribution(id:str,user=Depends(current_user),db=Depends(get_db)):
    db.delete(owned(db,Contribution,id,user.id)); db.commit()

@router.get("/recurring")
def recurring(user=Depends(current_user),db=Depends(get_db)):
    return serialize(db.scalars(select(Recurring).where(Recurring.user_id==user.id).order_by(Recurring.next_due)).all())

def check_recurring(db,data,user_id):
    a=owned(db,Account,data.account_id,user_id)
    if a.currency!=data.currency: raise HTTPException(422,"Account currency mismatch")
    if data.category_id: owned(db,Category,data.category_id,user_id)

@router.post("/recurring",status_code=201)
def add_recurring(data:RecurringIn,user=Depends(current_user),db=Depends(get_db)):
    check_recurring(db,data,user.id)
    row=Recurring(user_id=user.id,anchor_day=data.next_due.day,**data.model_dump()); db.add(row); db.commit(); return serialize(row)

@router.put("/recurring/{id}")
def edit_recurring(id:str,data:RecurringIn,user=Depends(current_user),db=Depends(get_db)):
    row=owned(db,Recurring,id,user.id,True); check_recurring(db,data,user.id)
    for k,v in data.model_dump().items(): setattr(row,k,v)
    row.anchor_day=data.next_due.day; db.commit(); return serialize(row)

@router.delete("/recurring/{id}",status_code=204)
def delete_recurring(id:str,user=Depends(current_user),db=Depends(get_db)):
    db.delete(owned(db,Recurring,id,user.id)); db.commit()

@router.post("/recurring/{id}/pay")
def pay(id:str,data:PayIn,user=Depends(current_user),db=Depends(get_db)):
    row=owned(db,Recurring,id,user.id,True)
    existing=db.get(BillPayment,(id,data.due_date))
    if existing: return {"transaction_id":existing.transaction_id,"already_paid":True}
    if not row.active or data.due_date!=row.next_due: raise HTTPException(409,"Schedule changed; refresh before paying")
    zone=ZoneInfo(db.get(Preference,user.id).timezone)
    if data.due_date>datetime.now(zone).date(): raise HTTPException(422,"Future bills remain projections; pay on or after due date")
    tx=save_transaction(db,TransactionIn(kind=row.kind,amount=row.amount,currency=row.currency,occurred_at=datetime.combine(data.due_date,time(12),zone),account_id=row.account_id,category_id=row.category_id,merchant=row.name),user.id)
    db.add(BillPayment(recurring_id=id,due_date=data.due_date,transaction_id=tx.id))
    if row.frequency in ("daily","weekly"): row.next_due+=timedelta(days=1 if row.frequency=="daily" else 7)
    else:
        row.next_due+=relativedelta(months={"monthly":1,"quarterly":3,"yearly":12}[row.frequency])
        row.next_due=row.next_due.replace(day=min(row.anchor_day,monthrange(row.next_due.year,row.next_due.month)[1]))
    db.commit(); return {"transaction_id":tx.id,"already_paid":False}

@router.get("/holdings")
def holdings(user=Depends(current_user),db=Depends(get_db)): return serialize(db.scalars(select(Holding).where(Holding.user_id==user.id)).all())

@router.post("/holdings",status_code=201)
def add_holding(data:HoldingIn,user=Depends(current_user),db=Depends(get_db)):
    row=Holding(user_id=user.id,**data.model_dump()); db.add(row); db.commit(); return serialize(row)

@router.put("/holdings/{id}")
def edit_holding(id:str,data:HoldingIn,user=Depends(current_user),db=Depends(get_db)):
    row=owned(db,Holding,id,user.id)
    for k,v in data.model_dump().items(): setattr(row,k,v)
    db.commit(); return serialize(row)

@router.delete("/holdings/{id}",status_code=204)
def delete_holding(id:str,user=Depends(current_user),db=Depends(get_db)):
    db.delete(owned(db,Holding,id,user.id)); db.commit()

@router.post("/snapshots")
def snapshot(currency:str="INR",user=Depends(current_user),db=Depends(get_db)):
    day=datetime.now(ZoneInfo(db.get(Preference,user.id).timezone)).date()
    row=db.scalar(select(Snapshot).where(Snapshot.user_id==user.id,Snapshot.date==day,Snapshot.currency==currency))
    worth=net_worth(db,user.id,currency)
    if row: row.assets=worth["assets"]; row.liabilities=worth["liabilities"]
    else: row=Snapshot(user_id=user.id,date=day,currency=currency,assets=worth["assets"],liabilities=worth["liabilities"]); db.add(row)
    db.commit(); return serialize(row)

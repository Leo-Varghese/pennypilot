from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import select, func
from ..models import Budget, Allocation, Category, Goal, Contribution, Holding, Preference
from .ledger import base_query, totals, balances, ZERO

def budget_view(db,budget,zone,depth=0):
    if depth>120: raise ValueError("Rollover chain exceeds 120 periods")
    previous={}
    if budget.rollover and budget.previous_id:
        prior=db.get(Budget,budget.previous_id)
        if prior and prior.user_id==budget.user_id:
            previous={a["category_id"]:a["remaining"] for a in budget_view(db,prior,zone,depth+1)["allocations"]}
    result=[]
    from ..models import Transaction
    for allocation in db.scalars(select(Allocation).where(Allocation.budget_id==budget.id)):
        cat=db.get(Category,allocation.category_id)
        ids=[cat.id]+list(db.scalars(select(Category.id).where(Category.user_id==budget.user_id,Category.parent_id==cat.id)))
        spent=totals(db,base_query(budget.user_id,budget.currency,budget.start_date,budget.end_date,zone).where(Transaction.category_id.in_(ids)))["expenses"]
        carry=previous.get(cat.id,ZERO)
        limit=allocation.amount+carry
        result.append({"category_id":cat.id,"category":cat.name,"allocated":allocation.amount,"rollover":carry,"available":limit,"spent":spent,"remaining":limit-spent,"alert":spent>=limit*Decimal("0.8") if limit>0 else spent>0})
    from ..serialization import serialize
    return {**serialize(budget),"allocations":result,"allocated":sum((a["allocated"] for a in result),ZERO),"spent":sum((a["spent"] for a in result),ZERO),"remaining":sum((a["remaining"] for a in result),ZERO)}

def goal_view(db,goal):
    from ..serialization import serialize
    contributions=db.scalars(select(Contribution).where(Contribution.goal_id==goal.id,Contribution.user_id==goal.user_id).order_by(Contribution.date)).all()
    current=sum((c.amount for c in contributions),ZERO)
    months=max(1,(goal.target_date.year-date.today().year)*12+goal.target_date.month-date.today().month) if goal.target_date else None
    return {**serialize(goal),"current_amount":current,"progress":(current/goal.target_amount*100).quantize(Decimal("0.01")),"monthly_needed":(max(ZERO,goal.target_amount-current)/months).quantize(Decimal("0.01")) if months else None,"contributions":serialize(contributions)}

def net_worth(db,user_id,currency):
    rows=balances(db,user_id,currency)
    assets=sum((max(ZERO,a["balance"]) for a in rows),ZERO)
    liabilities=sum((max(ZERO,-a["balance"]) for a in rows),ZERO)
    for h in db.scalars(select(Holding).where(Holding.user_id==user_id,Holding.currency==currency)):
        if h.kind=="asset": assets+=h.amount
        else: liabilities+=h.amount
    return {"assets":assets,"liabilities":liabilities,"net_worth":assets-liabilities}

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from ..db import get_db
from ..models import *
from ..security import current_user
from ..serialization import serialize
from ..services.ledger import base_query, totals, balances, ZERO
from ..services.planning import budget_view, goal_view, net_worth
router=APIRouter()

@router.get("/dashboard")
@router.get("/analytics")
def dashboard(start:date,end:date,currency:str="INR",user=Depends(current_user),db=Depends(get_db)):
    pref=db.get(Preference,user.id); zone=ZoneInfo(pref.timezone)
    stmt=base_query(user.id,currency,start,end,pref.timezone)
    count=db.scalar(select(func.count()).select_from(stmt.subquery()))
    if count>50000: raise HTTPException(422,"Narrow analytics to 50,000 records")
    summary=totals(db,stmt)
    days=(end-start).days+1
    previous_start=start-timedelta(days=days); previous_end=start-timedelta(days=1)
    previous=totals(db,base_query(user.id,currency,previous_start,previous_end,pref.timezone))
    cats={c.id:c for c in db.scalars(select(Category).where(Category.user_id==user.id))}
    category=defaultdict(lambda:ZERO); merchant=defaultdict(lambda:ZERO); sources=defaultdict(lambda:ZERO)
    weekdays=defaultdict(lambda:ZERO); daily=defaultdict(lambda:{"income":ZERO,"expenses":ZERO})
    category_time=defaultdict(lambda:ZERO)
    for tx in db.scalars(stmt.order_by(Transaction.occurred_at)):
        dt=tx.occurred_at if tx.occurred_at.tzinfo else tx.occurred_at.replace(tzinfo=timezone.utc)
        local=dt.astimezone(zone); day=local.date().isoformat()
        if tx.kind=="income": daily[day]["income"]+=tx.amount; sources[tx.merchant]+=tx.amount
        if tx.kind in ("expense","refund"):
            amount=tx.amount if tx.kind=="expense" else -tx.amount
            daily[day]["expenses"]+=amount; category[tx.category_id]+=amount; merchant[tx.merchant]+=amount; weekdays[local.strftime("%A")]+=amount
            category_time[(day,tx.category_id)]+=amount
    series=[]
    for day,values in sorted(daily.items()):
        i,e=values["income"],values["expenses"]
        series.append({"date":day,**values,"savings":i-e,"cash_flow":i-e,"savings_rate":((i-e)/i*100).quantize(Decimal("0.01")) if i>0 else None})
    previous_categories=defaultdict(lambda:ZERO)
    for tx in db.scalars(base_query(user.id,currency,previous_start,previous_end,pref.timezone)):
        if tx.kind in ("expense","refund"): previous_categories[tx.category_id]+=tx.amount if tx.kind=="expense" else -tx.amount
    catrows=[{"id":id or "uncategorized","name":cats[id].name if id in cats else "Uncategorized","parent_id":cats[id].parent_id if id in cats else None,"amount":value,"previous":previous_categories[id],"change":value-previous_categories[id]} for id,value in sorted(category.items(),key=lambda x:x[1],reverse=True)]
    budgetrows=[budget_view(db,b,pref.timezone) for b in db.scalars(select(Budget).where(Budget.user_id==user.id,Budget.currency==currency,Budget.start_date<=end,Budget.end_date>=start))]
    goalrows=[goal_view(db,g) for g in db.scalars(select(Goal).where(Goal.user_id==user.id,Goal.currency==currency))]
    today=datetime.now(zone).date()
    upcoming=db.scalars(select(Recurring).where(Recurring.user_id==user.id,Recurring.currency==currency,Recurring.active==True,Recurring.next_due<=today+timedelta(days=30)).order_by(Recurring.next_due)).all()
    snapshots=db.scalars(select(Snapshot).where(Snapshot.user_id==user.id,Snapshot.currency==currency,Snapshot.date>=start,Snapshot.date<=end).order_by(Snapshot.date)).all()
    current_balances=balances(db,user.id,currency)
    # Projection includes all schedule occurrences over the next 30 days, not paid transactions.
    from dateutil.relativedelta import relativedelta
    from calendar import monthrange
    projected=[]
    for rule in upcoming:
        due=rule.next_due
        for _ in range(400):
            if due>today+timedelta(days=30): break
            if due>=today: projected.append({"date":due,"name":rule.name,"kind":rule.kind,"amount":rule.amount})
            if rule.frequency in ("daily","weekly"): due+=timedelta(days=1 if rule.frequency=="daily" else 7)
            else:
                due+=relativedelta(months={"monthly":1,"quarterly":3,"yearly":12}[rule.frequency]); due=due.replace(day=min(rule.anchor_day,monthrange(due.year,due.month)[1]))
    allocated=sum((b["allocated"] for b in budgetrows),ZERO)
    return serialize({"currency":currency,"timezone":pref.timezone,"period":{"start":start,"end":end},"comparison_period":{"start":previous_start,"end":previous_end},"totals":summary,"previous":previous,"accounts":current_balances,"budgets":budgetrows,"budget_remaining":sum((b["remaining"] for b in budgetrows),ZERO),"goals":goalrows,"upcoming":upcoming,"projection":projected,"net_worth":net_worth(db,user.id,currency),"net_worth_history":[{"date":s.date,"net_worth":s.assets-s.liabilities} for s in snapshots],"series":series,"categories":catrows,"merchants":[{"name":k,"amount":v} for k,v in sorted(merchant.items(),key=lambda x:x[1],reverse=True)],"income_sources":[{"name":k,"amount":v} for k,v in sources.items()],"weekdays":[{"name":k,"amount":weekdays[k]} for k in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]],"category_time":[{"date":d,"category_id":c or "uncategorized","name":cats[c].name if c in cats else "Uncategorized","amount":v} for (d,c),v in sorted(category_time.items(),key=lambda x:x[0][0])],"zero_based":{"enabled":pref.zero_based,"period_income":summary["income"],"allocated":allocated,"unassigned_income":summary["income"]-allocated},"insights":[{"category":c["name"],"increase":c["change"]} for c in catrows if c["change"]>0],"definitions":{"actual_savings":"Recorded income minus expenses net of refunds. Not a bank-balance change. Transfers, adjustments, goal allocations and projections excluded.","budget_remaining":"Sum of full-period remaining budgets overlapping this filter. Avoid overlapping budgets to prevent duplicate allocations.","net_worth":"Current account balances plus separately configured assets minus liabilities. Do not duplicate account values in holdings."}})

@router.get("/exports/data.json")
def data_export(user=Depends(current_user),db=Depends(get_db)):
    from ..routers.transactions import tx_out
    from fastapi.responses import JSONResponse
    data={"preferences":serialize(db.get(Preference,user.id)),"transactions":[tx_out(db,t) for t in db.scalars(select(Transaction).where(Transaction.user_id==user.id))]}
    for model in [Account,Category,Tag,Budget,Goal,Contribution,Recurring,Holding,Snapshot,ImportBatch]:
        data[model.__tablename__]=serialize(db.scalars(select(model).where(model.user_id==user.id)).all())
    data["allocations"]=serialize(db.scalars(select(Allocation).where(Allocation.budget_id.in_(select(Budget.id).where(Budget.user_id==user.id)))).all())
    data["bill_payments"]=serialize(db.scalars(select(BillPayment).where(BillPayment.recurring_id.in_(select(Recurring.id).where(Recurring.user_id==user.id)))).all())
    import base64
    data["receipts"]=[{"transaction_id":r.transaction_id,"content_type":r.content_type,"base64":base64.b64encode(r.data).decode()} for r in db.scalars(select(Receipt).where(Receipt.user_id==user.id))]
    return JSONResponse(data,headers={"Content-Disposition":"attachment; filename=pennypilot-data.json","Cache-Control":"no-store"})

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

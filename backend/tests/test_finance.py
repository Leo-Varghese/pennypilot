from decimal import Decimal
from datetime import date
import csv,io
from app.services.ledger import bounds
from app.db import SessionLocal
from app.models import User
from sqlalchemy import select

P="/api/v1"
def tx(client,auth,account,kind="expense",amount="100.00",**kwargs):
    data={"kind":kind,"amount":amount,"account_id":account,"currency":"INR","occurred_at":"2026-10-10T12:00:00+05:30",**kwargs}
    response=client.post(P+"/transactions",headers=auth,json=data)
    assert response.status_code==201,response.text
    return response.json()

def dashboard(client,auth,**params):
    response=client.get(P+"/dashboard",headers=auth,params={"start":"2026-10-01","end":"2026-10-31","currency":"INR",**params})
    assert response.status_code==200,response.text
    return response.json()

def test_auth_password_and_logout(client,auth):
    assert client.get(P+"/accounts").status_code==401
    with SessionLocal() as db:
        user=db.scalar(select(User)); assert user.password_hash.startswith("$argon2")
    r=client.post(P+"/auth/login",json={"email":"leo@example.com","password":"correct-horse-battery-123"}); assert r.status_code==200
    assert client.post(P+"/auth/logout",headers=auth).status_code==204
    assert client.get(P+"/accounts",headers=auth).status_code==401

def test_income_expense_refund_transfer_credit_card(client,auth,account):
    card=client.post(P+"/accounts",headers=auth,json={"name":"Card","type":"credit_card","opening_date":"2025-01-01"}).json()["id"]
    tx(client,auth,account,"income","10000.00")
    tx(client,auth,card,"expense","2000.00",payment_method="credit_card")
    tx(client,auth,account,"expense","500.00")
    tx(client,auth,card,"refund","200.00")
    tx(client,auth,account,"transfer","1800.00",destination_id=card)
    tx(client,auth,account,"adjustment","50.00",adjustment_direction=-1)
    d=dashboard(client,auth)
    assert Decimal(d["totals"]["income"])==10000
    assert Decimal(d["totals"]["expenses"])==2300
    assert Decimal(d["totals"]["actual_savings"])==7700
    assert Decimal(d["totals"]["savings_rate"])==77
    balances={a["id"]:Decimal(a["balance"]) for a in d["accounts"]}
    assert balances[card]==0
    assert balances[account]==8650
    assert sum(Decimal(s["expenses"]) for s in d["series"])==2300
    assert sum(Decimal(c["amount"]) for c in d["categories"])==2300

def test_transaction_crud_duplicate_tags(client,auth,account):
    row=tx(client,auth,account,tags=["college","food"],purpose="Lunch")
    data={k:v for k,v in row.items() if k in ["kind","amount","currency","occurred_at","account_id","destination_id","category_id","merchant","payment_method","location","purpose","notes","tags","adjustment_direction"]}
    data["amount"]="250.50"
    r=client.put(P+"/transactions/"+row["id"],headers=auth,json=data); assert r.status_code==200,r.text
    assert Decimal(dashboard(client,auth)["totals"]["expenses"])==Decimal("250.50")
    r=client.post(P+"/transactions/"+row["id"]+"/duplicate",headers=auth); assert r.status_code==201,r.text
    assert client.get(P+"/transactions?tag=college",headers=auth).json()["total"]==2
    assert client.delete(P+"/transactions/"+row["id"],headers=auth).status_code==204
    assert client.get(P+"/transactions/"+row["id"],headers=auth).status_code==404

def test_budgets_rollover_goals(client,auth,account):
    cat=client.get(P+"/categories",headers=auth).json()[0]["id"]
    tx(client,auth,account,amount="300.00",category_id=cat)
    data={"name":"October","start_date":"2026-10-01","end_date":"2026-10-31","allocations":[{"category_id":cat,"amount":"1000.00"}]}
    r=client.post(P+"/budgets",headers=auth,json=data); assert r.status_code==201,r.text
    b=r.json(); assert Decimal(b["remaining"])==700
    data.update(name="November",start_date="2026-11-01",end_date="2026-11-30",rollover=True,previous_id=b["id"])
    r=client.post(P+"/budgets",headers=auth,json=data); assert r.status_code==201,r.text
    assert Decimal(r.json()["remaining"])==1700
    g=client.post(P+"/goals",headers=auth,json={"name":"Laptop","target_amount":"50000.00","target_date":"2027-10-01"}).json()
    r=client.post(P+"/goals/"+g["id"]+"/contributions",headers=auth,json={"amount":"5000.00","date":"2025-01-01"}); assert r.status_code==201,r.text
    assert Decimal(r.json()["progress"])==10
    assert Decimal(dashboard(client,auth)["totals"]["expenses"])==300

def test_timezone_and_boundaries(client,auth,account):
    tx(client,auth,account,amount="10.00",occurred_at="2026-09-30T18:29:59Z")
    tx(client,auth,account,amount="20.00",occurred_at="2026-09-30T18:30:00Z")
    tx(client,auth,account,amount="30.00",occurred_at="2026-10-31T18:30:00Z")
    assert Decimal(dashboard(client,auth)["totals"]["expenses"])==20
    a,b=bounds(date(2026,3,8),date(2026,3,8),"America/New_York")
    assert (b-a).total_seconds()==23*3600
    assert client.get(P+"/dashboard?start=2026-10-31&end=2026-10-01",headers=auth).status_code==422

def test_cross_user_isolation(client,auth,account):
    row=tx(client,auth,account)
    token=client.post(P+"/auth/register",json={"email":"other@example.com","password":"another-secure-password"}).json()["access_token"]
    other={"Authorization":"Bearer "+token}
    assert client.get(P+"/transactions/"+row["id"],headers=other).status_code==404
    assert client.delete(P+"/transactions/"+row["id"],headers=other).status_code==404
    assert client.post(P+"/transactions",headers=other,json={"kind":"expense","amount":"1.00","account_id":account,"occurred_at":"2026-10-01T00:00:00Z"}).status_code==404
    assert client.get(P+"/accounts",headers=other).json()==[]
    assert dashboard(client,other)["categories"]==[]

def test_csv_atomic_import_export_duplicates(client,auth,account):
    raw=f"kind,amount,account_id,occurred_at,merchant\nexpense,123.45,{account},2026-10-02T12:00:00+05:30,Shop\n"
    r=client.post(P+"/imports/csv",headers=auth,files={"file":("data.csv",raw,"text/csv")}); assert r.status_code==201,r.text
    assert client.post(P+"/imports/csv",headers=auth,files={"file":("data.csv",raw,"text/csv")}).status_code==409
    exported=client.get(P+"/exports/transactions.csv",headers=auth); assert exported.status_code==200
    rows=list(csv.DictReader(io.StringIO(exported.content.decode("utf-8-sig")))); assert rows[0]["amount"]=="123.45"
    invalid=raw+f"expense,-1,{account},2026-10-02T12:00:00Z,Bad\n"
    assert client.post(P+"/imports/csv",headers=auth,files={"file":("bad.csv",invalid,"text/csv")}).status_code==422
    assert client.get(P+"/transactions",headers=auth).json()["total"]==1

def test_recurring_idempotent_paid_only(client,auth,account):
    r=client.post(P+"/recurring",headers=auth,json={"name":"Internet","amount":"499.00","account_id":account,"next_due":"2026-01-31","frequency":"monthly"}); assert r.status_code==201,r.text
    rule=r.json(); assert Decimal(dashboard(client,auth,start="2026-01-01",end="2026-01-31")["totals"]["expenses"])==0
    path=P+"/recurring/"+rule["id"]+"/pay"
    first=client.post(path,headers=auth,json={"due_date":"2026-01-31"}); assert first.status_code==200,first.text
    second=client.post(path,headers=auth,json={"due_date":"2026-01-31"}); assert second.json()["already_paid"]
    assert first.json()["transaction_id"]==second.json()["transaction_id"]
    assert client.get(P+"/recurring",headers=auth).json()[0]["next_due"]=="2026-02-28"
    assert client.get(P+"/transactions",headers=auth).json()["total"]==1

def test_currency_validation_and_decimal(client,auth,account):
    r=client.post(P+"/transactions",headers=auth,json={"kind":"expense","amount":"0.001","account_id":account,"occurred_at":"2026-10-01T00:00:00Z"}); assert r.status_code==422
    tx(client,auth,account,amount="0.10"); tx(client,auth,account,amount="0.20")
    assert Decimal(dashboard(client,auth)["totals"]["expenses"])==Decimal("0.30")
    assert Decimal(dashboard(client,auth,currency="USD")["totals"]["expenses"])==0

def test_cors_and_diagnostics(client):
    assert client.get("/health").json()=={"status":"ok"}
    r=client.options(P+"/accounts",headers={"Origin":"http://localhost:3000","Access-Control-Request-Method":"GET","Access-Control-Request-Headers":"Authorization"})
    assert r.status_code==200 and r.headers["access-control-allow-origin"]=="http://localhost:3000"
    r=client.options(P+"/accounts",headers={"Origin":"https://evil.invalid","Access-Control-Request-Method":"GET"}); assert r.status_code==400

def test_receipt_private_and_safe(client,auth,account):
    row=tx(client,auth,account); path=P+"/transactions/"+row["id"]+"/receipt"
    assert client.put(path,headers=auth,files={"file":("bad.svg",b"<svg></svg>","image/svg+xml")}).status_code==422
    r=client.put(path,headers=auth,files={"file":("receipt.png",b"\x89PNG\r\n\x1a\nsynthetic-test","image/png")}); assert r.status_code==200,r.text
    assert client.get(path).status_code==401
    assert client.get(path,headers=auth).status_code==200

def test_export_and_account_deletion(client,auth,account):
    tx(client,auth,account)
    r=client.get(P+"/exports/data.json",headers=auth); assert r.status_code==200,r.text
    assert len(r.json()["transactions"])==1 and "password_hash" not in r.text
    r=client.request("DELETE",P+"/auth/me",headers=auth,json={"email":"leo@example.com","password":"correct-horse-battery-123"}); assert r.status_code==204,r.text
    assert client.get(P+"/accounts",headers=auth).status_code==401


def test_search_preferences_and_filtered_export(client,auth,account):
    tx(client,auth,account,merchant="Campus cafe",purpose="Lunch")
    r=client.get(P+"/transactions?q=Campus",headers=auth)
    assert r.status_code==200,r.text
    assert r.json()["total"]==1
    p=client.get(P+"/preferences",headers=auth).json()
    assert "user_id" not in p
    assert client.put(P+"/preferences",headers=auth,json=p).status_code==200
    assert client.get(P+"/exports/transactions.csv?sort=amount_desc&q=Campus",headers=auth).status_code==200

def test_auth_rate_limit(client):
    data={"email":"unknown@example.com","password":"a-valid-length-password"}
    for _ in range(10): assert client.post(P+"/auth/login",json=data).status_code==401
    assert client.post(P+"/auth/login",json=data).status_code==429

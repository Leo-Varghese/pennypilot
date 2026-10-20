import csv, io, json, hashlib
from datetime import date, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response
from sqlalchemy import select, func, or_
from pydantic import ValidationError
from ..db import get_db
from ..models import Transaction, Category, Tag, TransactionTag, Receipt, Preference, ImportBatch, BillPayment
from ..schemas import TransactionIn, BulkIn
from ..security import current_user
from ..services.ledger import owned, base_query, save_transaction
from ..serialization import serialize
router=APIRouter()

def tx_out(db,tx):
    out=serialize(tx)
    if tx.occurred_at.tzinfo is None: out["occurred_at"]=tx.occurred_at.replace(tzinfo=timezone.utc).isoformat()
    out["tags"]=list(db.scalars(select(Tag.name).join(TransactionTag,TransactionTag.tag_id==Tag.id).where(TransactionTag.transaction_id==tx.id)))
    out["has_receipt"]=db.scalar(select(Receipt.id).where(Receipt.transaction_id==tx.id)) is not None
    return out

def filtered(db,user,start,end,currency,q,kind,category_id,account_id,merchant,tag,payment_method):
    pref=db.get(Preference,user.id)
    if bool(start)!=bool(end): raise HTTPException(422,"Supply both start and end")
    stmt=base_query(user.id,currency or pref.currency,start,end,pref.timezone)
    if q:
        pattern="%"+q.replace("%","\\%").replace("_","\\_")+"%"
        stmt=stmt.where(or_(Transaction.merchant.ilike(pattern,escape="\\"),Transaction.purpose.ilike(pattern,escape="\\"),Transaction.notes.ilike(pattern,escape="\\")))
    if kind: stmt=stmt.where(Transaction.kind==kind)
    if category_id: stmt=stmt.where(Transaction.category_id.is_(None) if category_id=="uncategorized" else Transaction.category_id==category_id)
    if account_id: stmt=stmt.where(or_(Transaction.account_id==account_id,Transaction.destination_id==account_id))
    if merchant is not None: stmt=stmt.where(Transaction.merchant==merchant)
    if payment_method: stmt=stmt.where(Transaction.payment_method==payment_method)
    if tag: stmt=stmt.where(Transaction.id.in_(select(TransactionTag.transaction_id).join(Tag,Tag.id==TransactionTag.tag_id).where(Tag.user_id==user.id,Tag.name==tag)))
    return stmt

@router.get("/transactions")
def list_transactions(start:date|None=None,end:date|None=None,currency:str|None=None,q:str="",kind:str|None=None,category_id:str|None=None,account_id:str|None=None,merchant:str|None=None,tag:str|None=None,payment_method:str|None=None,page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),sort:str="date_desc",user=Depends(current_user),db=Depends(get_db)):
    stmt=filtered(db,user,start,end,currency,q,kind,category_id,account_id,merchant,tag,payment_method)
    orders={"date_desc":Transaction.occurred_at.desc(),"date_asc":Transaction.occurred_at.asc(),"amount_desc":Transaction.amount.desc(),"amount_asc":Transaction.amount.asc()}
    if sort not in orders: raise HTTPException(422,"Invalid sort")
    count=db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows=db.scalars(stmt.order_by(orders[sort],Transaction.id).offset((page-1)*page_size).limit(page_size)).all()
    return {"items":[tx_out(db,t) for t in rows],"total":count,"page":page,"page_size":page_size}

@router.post("/transactions",status_code=201)
@router.post("/transfers",status_code=201)
def create(data:TransactionIn,user=Depends(current_user),db=Depends(get_db)):
    tx=save_transaction(db,data,user.id); db.commit(); return tx_out(db,tx)

@router.post("/transactions/bulk-category")
def bulk(data:BulkIn,user=Depends(current_user),db=Depends(get_db)):
    if data.category_id: owned(db,Category,data.category_id,user.id)
    rows=[owned(db,Transaction,id,user.id) for id in set(data.ids)]
    if any(t.kind=="transfer" for t in rows): raise HTTPException(422,"Transfers cannot be categorized")
    for tx in rows: tx.category_id=data.category_id
    db.commit(); return {"updated":len(rows)}

@router.get("/transactions/{id}")
def detail(id:str,user=Depends(current_user),db=Depends(get_db)): return tx_out(db,owned(db,Transaction,id,user.id))

@router.put("/transactions/{id}")
def edit(id:str,data:TransactionIn,user=Depends(current_user),db=Depends(get_db)):
    tx=owned(db,Transaction,id,user.id)
    if db.scalar(select(BillPayment).where(BillPayment.transaction_id==id)): raise HTTPException(409,"Paid recurring records are immutable; reverse with a refund or adjustment")
    save_transaction(db,data,user.id,tx); db.commit(); return tx_out(db,tx)

@router.delete("/transactions/{id}",status_code=204)
def remove(id:str,user=Depends(current_user),db=Depends(get_db)):
    tx=owned(db,Transaction,id,user.id)
    if db.scalar(select(BillPayment).where(BillPayment.transaction_id==id)): raise HTTPException(409,"Paid recurring records cannot be deleted; reverse with a refund")
    db.delete(tx); db.commit()

@router.post("/transactions/{id}/duplicate",status_code=201)
def duplicate(id:str,user=Depends(current_user),db=Depends(get_db)):
    tx=owned(db,Transaction,id,user.id)
    data=TransactionIn.model_validate({k:v for k,v in tx_out(db,tx).items() if k in TransactionIn.model_fields})
    new=save_transaction(db,data,user.id); db.commit(); return tx_out(db,new)

@router.put("/transactions/{id}/receipt")
async def upload(id:str,file:UploadFile=File(...),user=Depends(current_user),db=Depends(get_db)):
    owned(db,Transaction,id,user.id); content=await file.read(2*1024*1024+1)
    if len(content)>2*1024*1024: raise HTTPException(413,"Receipt maximum is 2 MiB")
    detected="image/png" if content.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg" if content.startswith(b"\xff\xd8\xff") else None
    if not detected: raise HTTPException(422,"Only PNG and JPEG images are accepted")
    row=db.scalar(select(Receipt).where(Receipt.transaction_id==id,Receipt.user_id==user.id))
    if row: row.data=content; row.content_type=detected
    else: db.add(Receipt(user_id=user.id,transaction_id=id,data=content,content_type=detected))
    db.commit(); return {"uploaded":True}

@router.get("/transactions/{id}/receipt")
def receipt(id:str,user=Depends(current_user),db=Depends(get_db)):
    row=db.scalar(select(Receipt).where(Receipt.transaction_id==id,Receipt.user_id==user.id))
    if not row: raise HTTPException(404,"Receipt not found")
    return Response(row.data,media_type=row.content_type,headers={"Content-Disposition":"attachment; filename=receipt."+("png" if row.content_type=="image/png" else "jpg"),"Cache-Control":"no-store"})

@router.delete("/transactions/{id}/receipt",status_code=204)
def delete_receipt(id:str,user=Depends(current_user),db=Depends(get_db)):
    row=db.scalar(select(Receipt).where(Receipt.transaction_id==id,Receipt.user_id==user.id))
    if not row: raise HTTPException(404,"Receipt not found")
    db.delete(row); db.commit()

CSV_FIELDS=list(TransactionIn.model_fields)
def safe_cell(value):
    text=str(value if value is not None else "")
    return "'"+text if text.lstrip().startswith(("=","+","-","@","\t","\r")) else text

@router.get("/exports/transactions.csv")
def export_csv(sort:str="date_desc",start:date|None=None,end:date|None=None,currency:str|None=None,q:str="",kind:str|None=None,category_id:str|None=None,account_id:str|None=None,merchant:str|None=None,tag:str|None=None,payment_method:str|None=None,user=Depends(current_user),db=Depends(get_db)):
    stmt=filtered(db,user,start,end,currency,q,kind,category_id,account_id,merchant,tag,payment_method)
    if db.scalar(select(func.count()).select_from(stmt.subquery()))>50000: raise HTTPException(422,"Narrow export to 50,000 records")
    stream=io.StringIO(); writer=csv.DictWriter(stream,fieldnames=CSV_FIELDS); writer.writeheader()
    for tx in db.scalars(stmt.order_by(Transaction.occurred_at)):
        data=tx_out(db,tx); writer.writerow({k:safe_cell(json.dumps(data[k]) if k=="tags" else data[k]) for k in CSV_FIELDS})
    return Response("\ufeff"+stream.getvalue(),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=pennypilot-transactions.csv"})

@router.post("/imports/csv",status_code=201)
async def import_csv(file:UploadFile=File(...),user=Depends(current_user),db=Depends(get_db)):
    raw=await file.read(2*1024*1024+1)
    if len(raw)>2*1024*1024: raise HTTPException(413,"CSV maximum is 2 MiB")
    digest=hashlib.sha256(raw).hexdigest()
    if db.scalar(select(ImportBatch).where(ImportBatch.user_id==user.id,ImportBatch.digest==digest)): raise HTTPException(409,"This exact file was already imported")
    try:
        reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if not reader.fieldnames or not {"kind","amount","occurred_at","account_id"}.issubset(reader.fieldnames): raise ValueError("Missing required CSV headers")
        if set(reader.fieldnames)-set(CSV_FIELDS): raise ValueError("Unknown CSV headers")
        count=0
        for count,row in enumerate(reader,1):
            if count>5000: raise ValueError("Maximum 5,000 rows per import")
            row={k:v for k,v in row.items() if v not in ("",None)}
            if "tags" in row: row["tags"]=json.loads(row["tags"])
            save_transaction(db,TransactionIn.model_validate(row),user.id)
        if not count: raise ValueError("CSV has no records")
        db.add(ImportBatch(user_id=user.id,digest=digest,count=count)); db.commit(); return {"imported":count}
    except (ValueError,ValidationError,UnicodeDecodeError,csv.Error) as exc:
        db.rollback(); raise HTTPException(422,"Invalid CSV: "+str(exc)[:500])

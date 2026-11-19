import csv
import hashlib
import io
import re
from datetime import datetime, time, timezone
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_, select

from ..db import get_db
from ..models import Account, BankImportBatch, BankImportItem, Category, Preference, Transaction
from ..schemas import TransactionIn
from ..security import current_user
from ..services.ledger import owned, save_transaction
from ..serialization import serialize

router = APIRouter()
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_ROWS = 3000

DATE_FORMATS = (
    "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
    "%Y-%m-%d", "%d %b %Y", "%d-%b-%Y", "%d %B %Y",
)

class Mapping(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: str
    description: str
    debit: str | None = None
    credit: str | None = None
    amount: str | None = None
    direction: str | None = None
    reference: str | None = None
    balance: str | None = None

class CommitRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    row_number: int = Field(ge=1)
    selected: bool = True
    occurred_date: str
    description: str = Field(min_length=1, max_length=500)
    reference: str = Field(default="", max_length=160)
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=2)
    kind: str = Field(pattern="^(income|expense|refund)$")
    merchant: str = Field(default="", max_length=160)
    category_id: str | None = None
    payment_method: str = Field(default="bank_transfer", pattern="^(upi|cash|debit_card|credit_card|wallet|bank_transfer|other)$")
    fingerprint: str = Field(min_length=64, max_length=64)

class CommitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_id: str
    source_bank: str = Field(default="Bank CSV", min_length=1, max_length=100)
    file_name: str = Field(max_length=255)
    file_digest: str = Field(min_length=64, max_length=64)
    rows: list[CommitRow] = Field(min_length=1, max_length=MAX_ROWS)


def clean_money(value: str | None) -> Decimal | None:
    if value is None: return None
    text=str(value).strip().replace(",","").replace("â‚¹","").replace("INR","").strip()
    if not text or text in {"-","--"}: return None
    negative=text.startswith("(") and text.endswith(")")
    text=text.strip("()")
    try: amount=Decimal(text).quantize(Decimal("0.01"))
    except InvalidOperation: raise ValueError(f"Invalid amount: {value}")
    return -amount if negative else amount


def parse_date(value: str):
    text=value.strip()
    for fmt in DATE_FORMATS:
        try: return datetime.strptime(text,fmt).date()
        except ValueError: pass
    try: return datetime.fromisoformat(text).date()
    except ValueError: raise ValueError(f"Unsupported date: {value}")


def normalized(text: str): return re.sub(r"\s+"," ",text.strip().lower())

def merchant_from(description: str):
    text=re.sub(r"\b(upi|imps|neft|rtgs|txn|ref|payment|paid|to|from)\b"," ",description,flags=re.I)
    text=re.sub(r"[0-9@/_-]+"," ",text)
    return re.sub(r"\s+"," ",text).strip()[:160] or description[:160]

def payment_from(description: str):
    upper=description.upper()
    if "UPI" in upper:return "upi"
    if "ATM" in upper or "CASH" in upper:return "cash"
    if "CARD" in upper or "POS" in upper:return "debit_card"
    return "bank_transfer"

def fingerprint(user_id,account_id,date,amount,kind,description,reference):
    raw="|".join([user_id,account_id,str(date),format(amount,"f"),kind,normalized(description),normalized(reference)])
    return hashlib.sha256(raw.encode()).hexdigest()


def parse_rows(content: bytes, mapping: Mapping, user_id: str, account_id: str):
    try: text=content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try: text=content.decode("cp1252")
        except UnicodeDecodeError: raise HTTPException(422,"CSV must be UTF-8 or Windows-1252 text")
    reader=csv.DictReader(io.StringIO(text))
    if not reader.fieldnames: raise HTTPException(422,"CSV headers were not found")
    required={mapping.date,mapping.description}
    if mapping.amount: required.add(mapping.amount)
    elif mapping.debit and mapping.credit: required.update([mapping.debit,mapping.credit])
    else: raise HTTPException(422,"Map either Amount, or both Debit and Credit")
    missing=required-set(reader.fieldnames)
    if missing: raise HTTPException(422,"Missing mapped headers: "+", ".join(sorted(missing)))
    output=[]
    for number,row in enumerate(reader,2):
        if len(output)>=MAX_ROWS: raise HTTPException(413,f"Maximum {MAX_ROWS} statement rows")
        try:
            day=parse_date(row.get(mapping.date, ""))
            description=(row.get(mapping.description) or "").strip()
            reference=(row.get(mapping.reference) or "").strip() if mapping.reference else ""
            if not description: raise ValueError("Description is empty")
            if mapping.amount:
                value=clean_money(row.get(mapping.amount))
                if value is None or value==0: raise ValueError("Amount is empty or zero")
                direction=(row.get(mapping.direction) or "").strip().lower() if mapping.direction else ""
                if direction in {"debit","dr","d","withdrawal"}: kind="expense"; amount=abs(value)
                elif direction in {"credit","cr","c","deposit"}: kind="income"; amount=abs(value)
                elif value<0: kind="expense"; amount=abs(value)
                else: kind="income"; amount=value
            else:
                debit=clean_money(row.get(mapping.debit)) or Decimal(0)
                credit=clean_money(row.get(mapping.credit)) or Decimal(0)
                if debit>0 and credit>0: raise ValueError("Both debit and credit are populated")
                if debit>0: kind="expense"; amount=debit
                elif credit>0: kind="income"; amount=credit
                else: raise ValueError("Debit and credit are empty or zero")
            fp=fingerprint(user_id,account_id,day,amount,kind,description,reference)
            output.append({"row_number":number,"occurred_date":day.isoformat(),"description":description,"reference":reference,"amount":format(amount,"f"),"kind":kind,"merchant":merchant_from(description),"payment_method":payment_from(description),"fingerprint":fp,"error":None})
        except ValueError as exc:
            output.append({"row_number":number,"error":str(exc)[:240]})
    return output


@router.post("/bank-import/headers")
async def headers(file:UploadFile=File(...),user=Depends(current_user)):
    content=await file.read(MAX_FILE_BYTES+1)
    if len(content)>MAX_FILE_BYTES: raise HTTPException(413,"Statement maximum is 2 MiB")
    try:text=content.decode("utf-8-sig")
    except UnicodeDecodeError:text=content.decode("cp1252",errors="replace")
    reader=csv.reader(io.StringIO(text)); first=next(reader,None)
    if not first: raise HTTPException(422,"CSV is empty")
    return {"headers":[x.strip() for x in first],"file_name":file.filename or "statement.csv","file_digest":hashlib.sha256(content).hexdigest()}


@router.post("/bank-import/preview")
async def preview(account_id:str,mapping_json:str,file:UploadFile=File(...),user=Depends(current_user),db=Depends(get_db)):
    account=owned(db,Account,account_id,user.id)
    try:mapping=Mapping.model_validate_json(mapping_json)
    except Exception as exc: raise HTTPException(422,"Invalid column mapping") from exc
    content=await file.read(MAX_FILE_BYTES+1)
    if len(content)>MAX_FILE_BYTES: raise HTTPException(413,"Statement maximum is 2 MiB")
    rows=parse_rows(content,mapping,user.id,account.id)
    fingerprints=[r["fingerprint"] for r in rows if not r.get("error")]
    existing=set(db.scalars(select(BankImportItem.fingerprint).where(BankImportItem.user_id==user.id,BankImportItem.fingerprint.in_(fingerprints)))) if fingerprints else set()
    categories=db.scalars(select(Category).where(Category.user_id==user.id)).all()
    latest_by_merchant={}
    for tx in db.scalars(select(Transaction).where(Transaction.user_id==user.id,Transaction.kind!="transfer").order_by(Transaction.occurred_at.desc()).limit(2000)):
        key=normalized(tx.merchant)
        if key and key not in latest_by_merchant: latest_by_merchant[key]=tx.category_id
    for row in rows:
        if row.get("error"): row["status"]="invalid";continue
        row["status"]="already_imported" if row["fingerprint"] in existing else "new"
        row["category_id"]=latest_by_merchant.get(normalized(row["merchant"]))
    valid_dates=[r["occurred_date"] for r in rows if not r.get("error")]
    return {"file_name":file.filename or "statement.csv","file_digest":hashlib.sha256(content).hexdigest(),"account":serialize(account),"categories":serialize(categories),"rows":rows,"coverage":{"start":min(valid_dates) if valid_dates else None,"end":max(valid_dates) if valid_dates else None}}


@router.post("/bank-import/commit",status_code=201)
def commit(data:CommitRequest,user=Depends(current_user),db=Depends(get_db)):
    account=owned(db,Account,data.account_id,user.id,True)
    if db.scalar(select(BankImportBatch).where(BankImportBatch.user_id==user.id,BankImportBatch.file_digest==data.file_digest,BankImportBatch.account_id==account.id)):
        raise HTTPException(409,"This exact statement was already imported to this account")
    selected=[r for r in data.rows if r.selected]
    if not selected: raise HTTPException(422,"Select at least one new row")
    duplicates=set(db.scalars(select(BankImportItem.fingerprint).where(BankImportItem.user_id==user.id,BankImportItem.fingerprint.in_([r.fingerprint for r in selected]))))
    batch=BankImportBatch(user_id=user.id,account_id=account.id,source_bank=data.source_bank,file_name=data.file_name,file_digest=data.file_digest,row_count=0)
    db.add(batch);db.flush();created=[];skipped=0
    zone=ZoneInfo(db.get(Preference,user.id).timezone)
    for row in selected:
        if row.fingerprint in duplicates: skipped+=1;continue
        if row.category_id: owned(db,Category,row.category_id,user.id)
        try: local_date=datetime.fromisoformat(row.occurred_date).date()
        except ValueError: raise HTTPException(422,f"Invalid date on row {row.row_number}")
        tx=save_transaction(db,TransactionIn(kind=row.kind,amount=row.amount,currency=account.currency,occurred_at=datetime.combine(local_date,time(12),zone),account_id=account.id,category_id=row.category_id,merchant=row.merchant,payment_method=row.payment_method,purpose="Imported bank statement",notes=""),user.id)
        db.add(BankImportItem(user_id=user.id,batch_id=batch.id,transaction_id=tx.id,fingerprint=row.fingerprint,row_number=row.row_number,original_description=row.description,bank_reference=row.reference,statement_date=local_date))
        created.append(tx.id)
    batch.row_count=len(created)
    if not created: raise HTTPException(409,"All selected rows were already imported")
    db.commit()
    return {"batch_id":batch.id,"imported":len(created),"skipped_duplicates":skipped,"transaction_ids":created}


@router.get("/bank-import/batches")
def batches(user=Depends(current_user),db=Depends(get_db)):
    rows=db.scalars(select(BankImportBatch).where(BankImportBatch.user_id==user.id).order_by(BankImportBatch.created_at.desc()).limit(50)).all()
    return serialize(rows)


@router.delete("/bank-import/batches/{batch_id}")
def undo(batch_id:str,user=Depends(current_user),db=Depends(get_db)):
    batch=owned(db,BankImportBatch,batch_id,user.id,True)
    items=db.scalars(select(BankImportItem).where(BankImportItem.batch_id==batch.id,BankImportItem.user_id==user.id)).all()
    removed=0
    for item in items:
        tx=db.scalar(select(Transaction).where(Transaction.id==item.transaction_id,Transaction.user_id==user.id))
        if tx is not None: db.delete(tx);removed+=1
    db.delete(batch);db.commit()
    return {"undone":removed}
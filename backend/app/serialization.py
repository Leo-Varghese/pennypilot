from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import inspect

def serialize(v):
    if isinstance(v,Decimal): return format(v,"f")
    if isinstance(v,(date,datetime)): return v.isoformat()
    if isinstance(v,dict): return {k:serialize(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [serialize(x) for x in v]
    if hasattr(v,"__table__"): return {c.key:serialize(getattr(v,c.key)) for c in inspect(v).mapper.column_attrs if c.key not in {"password_hash","data","token_hash"}}
    return v

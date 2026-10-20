import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .config import settings
from .db import engine
from .routers import auth, transactions, resources, analytics

app=FastAPI(title="PennyPilot API",version="1.0.0",description="Decimal-based, user-isolated personal finance API. Money is serialized as strings.")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.frontend_origins.split(",")],allow_credentials=False,allow_methods=["GET","POST","PUT","DELETE","OPTIONS"],allow_headers=["Authorization","Content-Type"])

@app.middleware("http")
async def security_headers(request:Request,call_next):
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Referrer-Policy"]="no-referrer"
    response.headers["Cache-Control"]="no-store"
    if settings.app_env=="production": response.headers["Strict-Transport-Security"]="max-age=31536000; includeSubDomains"
    return response

@app.exception_handler(IntegrityError)
async def conflict(request,exc): return JSONResponse({"detail":"Record conflicts with existing data or is still referenced"},status_code=409)

@app.exception_handler(SQLAlchemyError)
async def database_error(request,exc):
    logging.error("Database request failed: %s",type(exc).__name__)
    return JSONResponse({"detail":"Database unavailable. Please retry."},status_code=503)

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")); conn.execute(text("SELECT version_num FROM alembic_version"))
        return {"status":"ready"}
    except Exception: return JSONResponse({"status":"not_ready"},status_code=503)

for router in [auth.router,transactions.router,resources.router,analytics.router]: app.include_router(router,prefix="/api/v1")

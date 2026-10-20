import os
from pathlib import Path
import pytest
os.environ.setdefault("DATABASE_URL","sqlite:////tmp/pennypilot-tests.db")
os.environ.setdefault("APP_ENV","test")
if "test" not in os.environ["DATABASE_URL"].rsplit("/",1)[-1].lower():
    raise RuntimeError("Tests require an explicitly named disposable test database")
from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, engine
from sqlalchemy import text

def reset():
    with engine.begin() as conn:
        if engine.dialect.name == "sqlite": conn.execute(text("PRAGMA foreign_keys=OFF"))
        Base.metadata.drop_all(conn)
        if engine.dialect.name == "sqlite": conn.execute(text("PRAGMA foreign_keys=ON"))

@pytest.fixture()
def client():
    reset()
    Base.metadata.create_all(engine)
    with TestClient(app) as c: yield c
    reset()

@pytest.fixture()
def auth(client):
    data={"email":"leo@example.com","password":"correct-horse-battery-123"}
    response=client.post("/api/v1/auth/register",json=data)
    assert response.status_code==201,response.text
    return {"Authorization":"Bearer "+response.json()["access_token"]}

@pytest.fixture()
def account(client,auth):
    response=client.post("/api/v1/accounts",headers=auth,json={"name":"Bank","type":"savings","opening_balance":"1000.00","opening_date":"2025-01-01"})
    assert response.status_code==201,response.text
    return response.json()["id"]

from .test_access import db, request
from unittest.mock import AsyncMock
from datetime import datetime, timezone, timedelta

def payload():
    return dict(nome="Novo agricultor", email="novo@example.com", password="new-password123",
        fazenda="Nova fazenda", municipio="Itapiranga / SC", num_suinos=20,
        area_m2=300, fonte_agua="Poço", hidrometro_serial="H-NEW")

def test_public_signup_creates_isolated_farmer_and_farm(db):
    before = len(db.propriedades.rows)
    response = request("POST", "/auth/cadastro", json=payload())
    assert response.status_code == 201
    user = response.json()
    assert user["role"] == "produtor" and user["ativo"] is True and "password_hash" not in user
    assert len(db.propriedades.rows) == before + 1
    assert user["propriedade_id"] not in ("a", "b")
    assert request("POST", "/auth/login", json={"email":payload()["email"],"password":payload()["password"]}).status_code == 200
    assert [p["id"] for p in request("GET", "/propriedades", user).json()] == [user["propriedade_id"]]
    assert request("GET", "/propriedades/a", user).status_code == 403
    assert request("GET", "/dashboard/prefeitura", user).status_code == 403

def test_signup_rejects_role_or_existing_farm_assignment(db):
    for field, value in [("role","prefeitura"),("propriedade_id","a"),("ativo",True)]:
        data = payload(); data[field] = value
        assert request("POST", "/auth/cadastro", json=data).status_code == 422
    assert len(db.propriedades.rows) == 2

def test_duplicate_does_not_create_another_farm(db):
    data = payload(); data["email"] = "A@example.com"
    assert request("POST", "/auth/cadastro", json=data).status_code == 409
    assert len(db.propriedades.rows) == 2 and len(db.users.rows) == 2

def test_signup_compensates_failed_farm_creation(db, monkeypatch):
    monkeypatch.setattr(db.propriedades,"insert_one",AsyncMock(side_effect=RuntimeError("write failed")))
    assert request("POST", "/auth/cadastro", json=payload()).status_code == 503
    assert len(db.users.rows) == 2 and len(db.propriedades.rows) == 2

def test_signup_is_rate_limited(db):
    for i in range(5):
        data=payload(); data["email"]=f"new{i}@example.com"
        assert request("POST", "/auth/cadastro", json=data).status_code == 201
    assert request("POST", "/auth/cadastro", json=payload()).status_code == 429

def test_signup_validates_fields(db):
    for field, value in [("password","short"),("nome","  "),("area_m2",-1),("num_suinos",-1)]:
        data=payload(); data[field]=value
        assert request("POST", "/auth/cadastro", json=data).status_code == 422

def test_expired_attempt_window_starts_fresh(db):
    db.login_attempts.rows.append({"identifier":"cadastro:127.0.0.1", "count":4,
        "locked_until":(datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat()})
    assert request("POST", "/auth/cadastro", json=payload()).status_code == 201
    assert db.login_attempts.rows[0]["count"] == 1

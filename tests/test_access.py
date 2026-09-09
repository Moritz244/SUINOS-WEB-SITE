"""HTTP-level authorization regression tests with an isolated in-memory database."""
import os
import sys
from pathlib import Path
from copy import deepcopy
import asyncio
import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.update(MONGO_URL="mongodb://localhost:27017", DB_NAME="test", JWT_SECRET="test-secret-" * 5, COOKIE_SECURE="false")
import server
import auth

class Cursor:
    def __init__(self, rows): self.rows = deepcopy(rows)
    def sort(self, *args): return self
    async def to_list(self, size): return self.rows if size is None else self.rows[:size]

class Collection:
    def __init__(self, rows=()): self.rows = deepcopy(list(rows))
    def find(self, q, projection=None): return Cursor([r for r in self.rows if all(r.get(k) == v for k, v in q.items())])
    async def find_one(self, q, projection=None):
        rows = await self.find(q).to_list(1)
        return rows[0] if rows else None
    async def insert_one(self, doc): self.rows.append(deepcopy(doc))
    async def delete_one(self, q): self.rows = [r for r in self.rows if not all(r.get(k) == v for k, v in q.items())]
    async def update_one(self, q, update, upsert=False):
        row = next((r for r in self.rows if all(r.get(k) == v for k, v in q.items())), None)
        matched = row is not None
        if row is None and upsert: row = dict(q); self.rows.append(row)
        if row is not None:
            row.update(update.get("$set", {}))
            for k, v in update.get("$inc", {}).items(): row[k] = row.get(k, 0) + v
        return type("Result", (), {"matched_count": int(matched)})()

class Database:
    def __init__(self):
        prop = dict(nome="Fazenda", municipio="Cidade", produtor_nome="Agricultor", num_suinos=10, area_m2=20, fonte_agua="Poço", hidrometro_serial="123", meta_reducao_pct=10)
        self.propriedades = Collection([{**prop, "id": "a"}, {**prop, "id": "b"}])
        self.users = Collection([{"id": "u", "email": "a@example.com", "role": "produtor", "propriedade_id": "a", "nome": "A", "password_hash": auth.hash_password("password123")}, {"id": "admin", "role": "prefeitura", "nome": "Admin", "email": "admin@example.com"}])
        self.alertas = Collection([dict(id="alert-b", propriedade_id="b", tipo="consumo_alto", severidade="alta", mensagem="Alerta", resolvido=False)])
        self.leituras = Collection([dict(id="read-b", propriedade_id="b", leitura_m3=10, consumo_m3=1, data_leitura="2026-01-01", foto_path="private-b")])
        self.dejetos = Collection()
        self.despesas = Collection([dict(id="expense-b", propriedade_id="b", valor_centavos=123, descricao="Energia", data="2026-01-01")])
        self.login_attempts = Collection()

@pytest.fixture
def db(monkeypatch):
    database = Database(); monkeypatch.setattr(server, "db", database); auth.bind_db(database)
    return database

def request(method, path, user=None, **kwargs):
    async def run():
        headers = {"X-Requested-With": "AquaSuino"}
        if user: headers["Authorization"] = "Bearer " + auth.create_access_token(user)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url="http://test") as client:
            return await client.request(method, "/api" + path, headers=headers, **kwargs)
    return asyncio.run(run())

@pytest.mark.parametrize("path", ["/propriedades", "/propriedades/a", "/leituras", "/dejetos", "/alertas", "/despesas", "/dashboard/prefeitura", "/dashboard/frivatti", "/relatorio/viabilidade", "/leituras/foto/private-b", "/auth/me"])
def test_anonymous_denied(db, path):
    assert request("GET", path).status_code == 401

@pytest.mark.parametrize("path", ["/propriedades/b", "/leituras?propriedade_id=b", "/dejetos?propriedade_id=b", "/alertas?propriedade_id=b", "/despesas?propriedade_id=b", "/leituras/foto/private-b", "/dashboard/prefeitura", "/dashboard/frivatti", "/relatorio/viabilidade"])
def test_farmer_cannot_read_other_farm(db, path):
    assert request("GET", path, db.users.rows[0]).status_code == 403

@pytest.mark.parametrize("path", ["/leituras", "/dejetos", "/alertas", "/despesas"])
def test_lists_are_scoped(db, path):
    assert request("GET", path, db.users.rows[0]).json() == []

def test_farmer_and_admin_properties(db):
    assert [p["id"] for p in request("GET", "/propriedades", db.users.rows[0]).json()] == ["a"]
    assert len(request("GET", "/propriedades", db.users.rows[1]).json()) == 2
    assert request("GET", "/propriedades/b", db.users.rows[1]).status_code == 200

def test_writes_are_scoped(db):
    user = db.users.rows[0]
    assert request("POST", "/alertas/alert-b/resolver", user).status_code == 403
    assert request("POST", "/leituras", user, data=dict(propriedade_id="b", leitura_m3="20", data_leitura="2026-01-01")).status_code == 403
    assert request("POST", "/dejetos", user, json=dict(propriedade_id="b", volume_kg=10, destino_digestato="x", destino_agua_tratada="y")).status_code == 403
    expense = dict(propriedade_id="b", descricao="Energia", valor="10.25", data="2026-01-01")
    assert request("POST", "/despesas", user, json=expense).status_code == 403
    expense["propriedade_id"] = "a"
    assert request("POST", "/despesas", user, json=expense).json()["valor_centavos"] == 1025
    expense["valor"] = "-1"
    assert request("POST", "/despesas", user, json=expense).status_code == 422

def test_login_cookie_and_logout(db):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url="http://test", headers={"X-Requested-With": "AquaSuino"}) as c:
            r = await c.post("/api/auth/login", json=dict(email="a@example.com", password="password123"))
            assert r.status_code == 200 and "password_hash" not in r.json()
            assert "HttpOnly" in r.headers["set-cookie"]
            assert (await c.get("/api/auth/me")).status_code == 200
            await c.post("/api/auth/logout")
            assert (await c.get("/api/auth/me")).status_code == 401
    asyncio.run(run())

def test_invalid_password_and_lockout(db):
    for _ in range(5): assert request("POST", "/auth/login", json=dict(email="a@example.com", password="wrong")).status_code == 401
    assert request("POST", "/auth/login", json=dict(email="a@example.com", password="password123")).status_code == 429

def test_account_creation_is_admin_only(db):
    payload = dict(nome="Novo", email="novo@example.com", password="password123", propriedade_id="a", role="prefeitura")
    assert request("POST", "/usuarios", db.users.rows[0], json=payload).status_code == 403
    r = request("POST", "/usuarios", db.users.rows[1], json=payload)
    assert r.status_code == 201 and r.json()["role"] == "produtor"
    assert "password_hash" not in r.json()

def test_csrf_header_required(db):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url="http://test") as c:
            assert (await c.post("/api/auth/logout")).status_code == 403
    asyncio.run(run())

def test_seed_not_public(db):
    assert request("POST", "/seed").status_code == 404

def test_prefeitura_consolidates_expenses(db):
    response = request("GET", "/dashboard/prefeitura", db.users.rows[1])
    assert response.status_code == 200
    data = response.json()
    assert data["despesas_total_centavos"] == 123
    assert {p["id"]: p["despesas_centavos"] for p in data["propriedades"]} == {"a": 0, "b": 123}

def test_deleted_account_loses_access(db):
    user = db.users.rows.pop(0)
    assert request("GET", "/propriedades", user).status_code == 401

def test_unassigned_account_has_no_data(db):
    user = db.users.rows[0]
    user["propriedade_id"] = None
    assert request("GET", "/propriedades", user).json() == []
    assert request("GET", "/despesas", user).json() == []
    assert request("GET", "/propriedades/a", user).status_code == 403

def test_reading_rejects_invalid_date_and_decreasing_meter(db):
    user=db.users.rows[0]
    db.leituras.rows.append(dict(id="own",propriedade_id="a",data_leitura="2026-01-01",leitura_m3=100,consumo_m3=0))
    assert request("POST","/leituras",user,data={"propriedade_id":"a","leitura_m3":"90","data_leitura":"2026-02-01"}).status_code==422
    assert request("POST","/leituras",user,data={"propriedade_id":"a","leitura_m3":"110","data_leitura":"invalid"}).status_code==422
    result=request("POST","/leituras",user,data={"propriedade_id":"a","leitura_m3":"120","data_leitura":"2026-02-01"})
    assert result.status_code==200 and result.json()["consumo_m3"]==20

from .test_access import db, request, auth, server
import asyncio
import httpx
import hashlib
from datetime import date, datetime, timezone, timedelta
from io import BytesIO
from pypdf import PdfReader
from management import farm_alerts

def test_users_are_admin_only_and_hide_secrets(db):
    assert request("GET", "/usuarios").status_code == 401
    assert request("GET", "/usuarios", db.users.rows[0]).status_code == 403
    data = request("GET", "/usuarios", db.users.rows[1]).json()
    assert len(data) == 2 and all("password_hash" not in u and "session_version" not in u for u in data)

def test_disable_revokes_and_reactivate_does_not_restore_old_session(db):
    async def run():
        token = auth.create_access_token(db.users.rows[0])
        admin = db.users.rows[1]
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url="http://test") as c:
            headers = {"Authorization": "Bearer " + auth.create_access_token(admin), "X-Requested-With":"AquaSuino"}
            assert (await c.patch("/api/usuarios/u/status", headers=headers,json={"ativo":False})).status_code == 200
            assert (await c.get("/api/propriedades", headers={"Authorization":"Bearer "+token})).status_code == 401
            assert (await c.post("/api/auth/login",headers={"X-Requested-With":"AquaSuino"},json={"email":"a@example.com","password":"password123"})).status_code == 401
            await c.patch("/api/usuarios/u/status",headers=headers,json={"ativo":True})
            assert (await c.get("/api/propriedades",headers={"Authorization":"Bearer "+token})).status_code == 401
    asyncio.run(run())

def test_admin_cannot_disable_admin_and_farmer_cannot_manage(db):
    assert request("PATCH", "/usuarios/admin/status",db.users.rows[1],json={"ativo":False}).status_code == 403
    assert request("PATCH", "/usuarios/u/status",db.users.rows[0],json={"ativo":False}).status_code == 403
    assert request("POST", "/usuarios/u/recuperacao",db.users.rows[0]).status_code == 403

def test_reset_single_use_and_replacement(db):
    first = request("POST", "/usuarios/u/recuperacao",db.users.rows[1]).json()["token"]
    token = request("POST", "/usuarios/u/recuperacao",db.users.rows[1]).json()["token"]
    assert db.users.rows[0]["reset_hash"] == hashlib.sha256(token.encode()).hexdigest()
    assert request("POST", "/auth/redefinir-senha",json={"token":first,"nova":"new-password123"}).status_code == 400
    assert request("POST", "/auth/redefinir-senha",json={"token":token,"nova":"new-password123"}).status_code == 200
    assert request("POST", "/auth/redefinir-senha",json={"token":token,"nova":"another-password"}).status_code == 400
    assert request("POST", "/auth/login",json={"email":"a@example.com","password":"password123"}).status_code == 401
    assert request("POST", "/auth/login",json={"email":"a@example.com","password":"new-password123"}).status_code == 200

def test_expired_reset_and_disabled_account(db):
    token = request("POST", "/usuarios/u/recuperacao",db.users.rows[1]).json()["token"]
    db.users.rows[0]["reset_expires"] = (datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
    assert request("POST", "/auth/redefinir-senha",json={"token":token,"nova":"new-password123"}).status_code == 400
    request("PATCH", "/usuarios/u/status",db.users.rows[1],json={"ativo":False})
    assert request("POST", "/usuarios/u/recuperacao",db.users.rows[1]).status_code == 409

def test_change_password_requires_current_and_revokes_sessions(db):
    user = db.users.rows[0]
    assert request("POST", "/auth/senha",user,json={"atual":"wrong","nova":"new-password123"}).status_code == 400
    old_token = auth.create_access_token(user)
    assert request("POST", "/auth/senha",user,json={"atual":"password123","nova":"new-password123"}).status_code == 200
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app),base_url="http://test") as c:
            assert (await c.get("/api/auth/me",headers={"Authorization":"Bearer "+old_token})).status_code == 401
    asyncio.run(run())

def test_delete_expense_access_and_totals(db):
    assert request("DELETE", "/despesas/expense-b").status_code == 401
    assert request("DELETE", "/despesas/expense-b",db.users.rows[0]).status_code == 403
    assert request("DELETE", "/despesas/expense-b",db.users.rows[1]).status_code == 200
    assert request("DELETE", "/despesas/expense-b",db.users.rows[1]).status_code == 404
    assert request("GET", "/dashboard/prefeitura",db.users.rows[1]).json()["despesas_total_centavos"] == 0
    db.despesas.rows.append(dict(id="own",propriedade_id="a",valor_centavos=100,data="2026-01-01",descricao="Teste"))
    assert request("DELETE", "/despesas/own",db.users.rows[0]).status_code == 200

def test_alert_boundaries_and_insufficient_data():
    prop = {"id":"a","nome":"Fazenda"}
    today = date(2026,9,8)
    assert farm_alerts(prop,[],[],today)[0]["tipo"] == "leitura_atrasada"
    readings = [{"data_leitura":"2026-08-04", "consumo_m3":100}]
    assert farm_alerts(prop,readings,[],today) == [] # exactly 35 days
    readings[0]["data_leitura"] = "2026-08-03"
    assert farm_alerts(prop,readings,[],today)[0]["tipo"] == "leitura_atrasada"
    readings = [{"data_leitura":"2026-08-01","consumo_m3":100},{"data_leitura":"2026-09-08","consumo_m3":115}]
    assert farm_alerts(prop,readings,[],today) == []
    readings[-1]["consumo_m3"] = 116
    assert farm_alerts(prop,readings,[],today)[0]["tipo"] == "consumo_alto"
    expenses = [{"data":"2026-08-01","valor_centavos":10000},{"data":"2026-07-01","valor_centavos":10000},{"data":"2026-09-01","valor_centavos":15001}]
    assert any(a["tipo"] == "despesa_alta" for a in farm_alerts(prop,readings,expenses,today))
    expenses[-1]["valor_centavos"] = 15000
    assert not any(a["tipo"] == "despesa_alta" for a in farm_alerts(prop,readings,expenses,today))

def test_attention_is_prefeitura_only(db):
    assert request("GET", "/dashboard/atencao",db.users.rows[0]).status_code == 403
    assert request("GET", "/dashboard/atencao",db.users.rows[1]).status_code == 200

def test_report_scope_period_and_escaped_text(db):
    assert request("GET", "/propriedades/a/relatorio").status_code == 401
    assert request("GET", "/propriedades/b/relatorio",db.users.rows[0]).status_code == 403
    assert request("GET", "/propriedades/a/relatorio?inicio=2026-09-01&fim=2026-08-01",db.users.rows[0]).status_code == 422
    db.despesas.rows.extend([dict(id="x",propriedade_id="a",data="2026-08-10",descricao="Incluída <ração> & milho",valor_centavos=12345),dict(id="y",propriedade_id="a",data="2026-09-01",descricao="Fora do período",valor_centavos=999)])
    response = request("GET", "/propriedades/a/relatorio?inicio=2026-08-01&fim=2026-08-31",db.users.rows[0])
    assert response.status_code == 200 and response.content.startswith(b"%PDF")
    text = "".join(p.extract_text() for p in PdfReader(BytesIO(response.content)).pages)
    assert "123,45" in text and "<ração> & milho" in text and "Fora do período" not in text and "Energia" not in text

"""Account lifecycle, municipal attention queue and individual farm reports."""
import hashlib
import secrets
import logging
import asyncio
from datetime import date, datetime, timedelta, timezone
from collections import defaultdict
from typing import Optional
from fastapi import Depends, HTTPException, Response, BackgroundTasks, Request
from pydantic import BaseModel, Field, EmailStr
from mailer import mail_settings, send_recovery_email
from auth import get_current_user, require_roles, public_user, hash_password, verify_password, check_lockout, register_failure, clear_failures

class PasswordChange(BaseModel):
    atual: str = Field(min_length=1, max_length=72)
    nova: str = Field(min_length=10, max_length=72)

class ResetPassword(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    nova: str = Field(min_length=10, max_length=72)

class AccountStatus(BaseModel):
    ativo: bool

class ForgotPassword(BaseModel):
    email: EmailStr

def valid_password(value):
    if len(value.encode("utf-8")) > 72:
        raise HTTPException(422, "A senha deve ter no máximo 72 bytes")
    return hash_password(value)

def month_shift(day, delta):
    total = day.year * 12 + day.month - 1 + delta
    return date(total // 12, total % 12 + 1, 1)

def farm_alerts(prop, readings, expenses, today):
    alerts = []
    def add(kind, severity, message):
        alerts.append({"id": f"{kind}:{prop['id']}", "tipo": kind, "severidade": severity,
                       "propriedade_id": prop["id"], "propriedade_nome": prop["nome"],
                       "mensagem": message})
    readings = sorted(readings, key=lambda r: r["data_leitura"])
    if not readings:
        add("leitura_atrasada", "alta", "Nenhuma leitura registrada. Cadastre a primeira leitura.")
    else:
        days = (today - date.fromisoformat(readings[-1]["data_leitura"][:10])).days
        if days > 35:
            add("leitura_atrasada", "alta", f"Última leitura há {days} dias. Prazo de acompanhamento: 35 dias.")
        previous = [r.get("consumo_m3", 0) for r in readings[-4:-1]]
        baseline = sum(previous) / len(previous) if previous else 0
        current = readings[-1].get("consumo_m3", 0)
        if baseline > 0 and current > round(baseline * 1.15, 6):
            add("consumo_alto", "alta", f"Último consumo: {current:.1f} m³; média das {len(previous)} leituras anteriores: {baseline:.1f} m³. Limite: 15% acima da média.")
    monthly = defaultdict(int)
    for expense in expenses:
        if expense["data"][:10] <= today.isoformat():
            monthly[expense["data"][:7]] += expense["valor_centavos"]
    prior = [monthly[month_shift(today, -i).isoformat()[:7]] for i in (1, 2, 3)]
    recorded = [v for v in prior if v > 0]
    current = monthly[today.isoformat()[:7]]
    if len(recorded) >= 2:
        average = sum(recorded) / len(recorded)
        if current > round(average * 1.5, 6):
            add("despesa_alta", "media", f"Despesas do mês: R$ {current / 100:.2f}; média dos meses com lançamentos nos últimos 3 meses: R$ {average / 100:.2f}. Limite: 50% acima da média; não é projeção mensal.")
    return alerts

def register_management(router, database, get_detail):
    # Resolve the DB via a provider so tests can replace it without opening MongoDB.
    def db():
        return database() if callable(database) else database

    async def deliver_reset(email):
        target = await db().users.find_one({"email": email})
        if not target or not target.get("ativo", True):
            return
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode()).hexdigest()
        expires = datetime.now(timezone.utc) + timedelta(minutes=30)
        await db().users.update_one({"id": target["id"]}, {"$set": {
            "reset_hash": digest, "reset_expires": expires.isoformat()}})
        try:
            await asyncio.to_thread(send_recovery_email, target["email"], target["nome"], token)
        except Exception:
            # Never log recipient addresses, reset tokens, message bodies or SMTP credentials.
            logging.getLogger(__name__).error("Falha no envio de recuperação por SMTP")
            await db().users.update_one({"id": target["id"], "reset_hash": digest}, {"$set": {"reset_hash": None}})

    @router.post("/auth/esqueci-senha", status_code=202)
    async def forgot_password(payload: ForgotPassword, request: Request, background: BackgroundTasks, response: Response):
        try:
            mail_settings()
        except (ValueError, TypeError):
            raise HTTPException(503, "O envio de e-mails ainda não está disponível. Entre em contato com a prefeitura.")
        ip = "recovery-ip:" + (request.client.host if request.client else "unknown")
        email = str(payload.email).lower().strip()
        identifier = "recovery-email:" + hashlib.sha256(email.encode()).hexdigest()
        await check_lockout(ip)
        await register_failure(ip)
        try:
            await check_lockout(identifier)
        except HTTPException:
            response.headers["Cache-Control"] = "no-store"
            return {"ok": True}
        await register_failure(identifier)
        background.add_task(deliver_reset, email)
        response.headers["Cache-Control"] = "no-store"
        return {"ok": True}

    @router.get("/usuarios")
    async def users(user=Depends(require_roles("prefeitura"))):
        docs = await db().users.find({}, {"_id": 0}).sort("nome", 1).to_list(None)
        return [public_user(doc) for doc in docs]

    async def managed_user(user_id):
        target = await db().users.find_one({"id": user_id})
        if not target:
            raise HTTPException(404, "Conta não encontrada")
        if target["role"] != "produtor":
            raise HTTPException(403, "A gestão de acesso é permitida somente para agricultores")
        return target

    @router.patch("/usuarios/{user_id}/status")
    async def status(user_id: str, payload: AccountStatus, user=Depends(require_roles("prefeitura"))):
        await managed_user(user_id)
        await db().users.update_one({"id": user_id}, {"$set": {"ativo": payload.ativo, "reset_hash": None}, "$inc": {"session_version": 1}})
        return {"ok": True}

    @router.post("/usuarios/{user_id}/recuperacao")
    async def recovery(user_id: str, response: Response, user=Depends(require_roles("prefeitura"))):
        target = await managed_user(user_id)
        if not target.get("ativo", True):
            raise HTTPException(409, "Ative a conta antes de gerar a recuperação")
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(minutes=30)
        await db().users.update_one({"id": user_id}, {"$set": {
            "reset_hash": hashlib.sha256(token.encode()).hexdigest(), "reset_expires": expires.isoformat()}})
        response.headers["Cache-Control"] = "no-store"
        return {"token": token, "expires_at": expires.isoformat()}

    @router.post("/auth/redefinir-senha")
    async def reset_password(payload: ResetPassword, response: Response):
        hashed_token = hashlib.sha256(payload.token.encode()).hexdigest()
        target = await db().users.find_one({"reset_hash": hashed_token})
        if not target or not target.get("ativo", True) or datetime.fromisoformat(target["reset_expires"]) <= datetime.now(timezone.utc):
            raise HTTPException(400, "Link inválido ou expirado. Solicite um novo em Esqueci minha senha.")
        result = await db().users.update_one({"id": target["id"], "reset_hash": hashed_token, "ativo": target.get("ativo")} if "ativo" in target else {"id": target["id"], "reset_hash": hashed_token},
            {"$set": {"password_hash": valid_password(payload.nova), "reset_hash": None}, "$inc": {"session_version": 1}})
        if not result.matched_count:
            raise HTTPException(400, "Link já utilizado ou revogado")
        await db().login_attempts.delete_one({"identifier": target["email"]})
        response.delete_cookie("access_token", path="/api")
        return {"ok": True}

    @router.post("/auth/senha")
    async def password(payload: PasswordChange, response: Response, user=Depends(get_current_user)):
        identifier = "password:" + user["id"]
        await check_lockout(identifier)
        if not verify_password(payload.atual, user["password_hash"]):
            await register_failure(identifier)
            raise HTTPException(400, "Senha atual incorreta")
        if payload.atual == payload.nova:
            raise HTTPException(422, "Escolha uma senha diferente da atual")
        result = await db().users.update_one({"id": user["id"], "password_hash": user["password_hash"]},
            {"$set": {"password_hash": valid_password(payload.nova), "reset_hash": None}, "$inc": {"session_version": 1}})
        if not result.matched_count:
            raise HTTPException(409, "A conta mudou. Entre novamente e tente outra vez.")
        await clear_failures(identifier)
        response.delete_cookie("access_token", path="/api")
        return {"ok": True}

    @router.get("/dashboard/atencao")
    async def attention(user=Depends(require_roles("prefeitura"))):
        props = await db().propriedades.find({}, {"_id": 0}).to_list(None)
        readings = await db().leituras.find({}, {"_id": 0}).to_list(None)
        expenses = await db().despesas.find({}, {"_id": 0}).to_list(None)
        by_reading, by_expense = defaultdict(list), defaultdict(list)
        for row in readings: by_reading[row["propriedade_id"]].append(row)
        for row in expenses: by_expense[row["propriedade_id"]].append(row)
        today = datetime.now(timezone.utc).date()
        alerts = [a for p in props for a in farm_alerts(p, by_reading[p["id"]], by_expense[p["id"]], today)]
        return {"data_referencia": today.isoformat(), "alertas": alerts}

    @router.get("/propriedades/{prop_id}/relatorio")
    async def report(prop_id: str, inicio: Optional[date] = None, fim: Optional[date] = None, user=Depends(get_current_user)):
        if inicio and fim and inicio > fim:
            raise HTTPException(422, "A data inicial deve ser anterior ou igual à final")
        detail = await get_detail(prop_id, user)
        expenses = await db().despesas.find({"propriedade_id": prop_id}, {"_id": 0}).sort("data", 1).to_list(None)
        def inside(value):
            day = date.fromisoformat(value[:10])
            return (not inicio or day >= inicio) and (not fim or day <= fim)
        detail["leituras"] = [r for r in detail["leituras"] if inside(r["data_leitura"])]
        detail["dejetos"] = [r for r in detail["dejetos"] if inside(r["data_registro"])]
        detail["despesas"] = [r for r in expenses if inside(r["data"])]
        from farm_report import build_farm_pdf
        content = build_farm_pdf(detail, inicio, fim)
        return Response(content, media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="relatorio-fazenda.pdf"', "Cache-Control": "no-store"})

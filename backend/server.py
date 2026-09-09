"""AquaSuíno backend — hydric + waste management for swine farms."""
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env.local")
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form, Response, Depends, Request
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional
from pathlib import Path
from datetime import datetime, timezone
from io import BytesIO
import os
import uuid
import logging

from storage import init_storage, put_object, get_object, MIME_TYPES, APP_NAME
from pdf_report import build_viability_pdf
from auth import (bind_db, get_current_user, require_roles, assert_prop_access,
                  public_user, verify_password, hash_password, create_access_token,
                  check_lockout, register_failure, clear_failures)
from pydantic import EmailStr
from pymongo.errors import DuplicateKeyError
from decimal import Decimal
from datetime import date


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]
bind_db(db)

app = FastAPI(title="AquaSuíno API")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ==================== MODELS ====================
class Propriedade(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    municipio: str
    produtor_nome: str
    num_suinos: int
    area_m2: float
    fonte_agua: str
    tem_biodigestor: bool = False
    adotou_tecnologia: bool = False
    hidrometro_serial: str
    meta_reducao_pct: int = 10
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PropriedadeCreate(BaseModel):
    nome: str
    municipio: str
    produtor_nome: str
    num_suinos: int
    area_m2: float
    fonte_agua: str
    tem_biodigestor: bool = False
    adotou_tecnologia: bool = False
    hidrometro_serial: str
    meta_reducao_pct: int = 10


class Leitura(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    propriedade_id: str
    leitura_m3: float
    consumo_m3: float = 0.0
    data_leitura: str
    foto_path: Optional[str] = None
    observacao: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Dejeto(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    propriedade_id: str
    volume_kg: float
    biogas_m3: float = 0.0
    destino_digestato: str
    destino_agua_tratada: str
    conforme_conama: bool = True
    data_registro: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DejetoCreate(BaseModel):
    propriedade_id: str
    volume_kg: float
    destino_digestato: str
    destino_agua_tratada: str
    conforme_conama: bool = True
    data_registro: Optional[str] = None


class Alerta(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    propriedade_id: str
    tipo: str
    severidade: str
    mensagem: str
    resolvido: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ==================== STARTUP ====================
@app.on_event("startup")
async def on_startup():
    if len(os.environ.get("JWT_SECRET", "")) < 32:
        raise RuntimeError("Configure JWT_SECRET com pelo menos 32 caracteres")
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier", unique=True)
    try:
        init_storage()
        logger.info("Object storage initialized")
    except Exception as e:
        logger.warning(f"Storage init failed at startup (will retry lazily): {e}")


@app.on_event("shutdown")
async def on_shutdown():
    client.close()


# ==================== HELPERS ====================
def _clean(doc):
    if doc and "_id" in doc:
        doc.pop("_id")
    return doc


async def _get_prop(prop_id: str):
    p = await db.propriedades.find_one({"id": prop_id}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Propriedade não encontrada")
    return p


async def _baseline_m3(prop_id: str) -> float:
    """Baseline = média das primeiras 3 leituras (ou todas se menos)."""
    leituras = await db.leituras.find(
        {"propriedade_id": prop_id}, {"_id": 0}
    ).sort("data_leitura", 1).to_list(3)
    if not leituras:
        return 0.0
    consumos = [l["consumo_m3"] for l in leituras if l.get("consumo_m3", 0) > 0]
    return sum(consumos) / len(consumos) if consumos else 0.0


# ==================== ENDPOINTS ====================
@api_router.get("/")
async def root():
    return {"app": "AquaSuíno", "status": "ok"}


# ---- Propriedades ----
@api_router.get("/propriedades", response_model=List[Propriedade])
async def list_propriedades(user=Depends(get_current_user)):
    q = {"id": user.get("propriedade_id")} if user["role"] == "produtor" else {}
    props = await db.propriedades.find(q, {"_id": 0}).sort("created_at", -1).to_list(None)
    return props


@api_router.post("/propriedades", response_model=Propriedade)
async def create_propriedade(payload: PropriedadeCreate, user=Depends(require_roles("prefeitura"))):
    prop = Propriedade(**payload.model_dump())
    await db.propriedades.insert_one(prop.model_dump())
    return prop


@api_router.get("/propriedades/{prop_id}")
async def get_propriedade(prop_id: str, user=Depends(get_current_user)):
    assert_prop_access(user, prop_id)
    prop = await _get_prop(prop_id)
    leituras = await db.leituras.find({"propriedade_id": prop_id}, {"_id": 0}).sort("data_leitura", 1).to_list(None)
    dejetos = await db.dejetos.find({"propriedade_id": prop_id}, {"_id": 0}).sort("data_registro", 1).to_list(None)
    alertas = await db.alertas.find({"propriedade_id": prop_id}, {"_id": 0}).sort("created_at", -1).to_list(None)
    baseline = await _baseline_m3(prop_id)
    total_consumo = sum(l.get("consumo_m3", 0) for l in leituras)
    total_biogas = sum(d.get("biogas_m3", 0) for d in dejetos)
    ultimo_consumo = leituras[-1]["consumo_m3"] if leituras else 0
    meta_m3 = baseline * (1 - prop["meta_reducao_pct"] / 100.0)
    economia_pct = ((baseline - ultimo_consumo) / baseline * 100) if baseline else 0
    bonus_estimado = max(0, (baseline - ultimo_consumo)) * 12 * 0.35 + total_biogas * 0.8
    return {
        "propriedade": prop,
        "leituras": leituras,
        "dejetos": dejetos,
        "alertas": alertas,
        "resumo": {
            "baseline_m3": round(baseline, 2),
            "meta_m3": round(meta_m3, 2),
            "ultimo_consumo_m3": round(ultimo_consumo, 2),
            "total_consumo_m3": round(total_consumo, 2),
            "total_biogas_m3": round(total_biogas, 2),
            "economia_pct": round(economia_pct, 1),
            "bonus_estimado_brl": round(bonus_estimado, 2),
            "alertas_ativos": sum(1 for a in alertas if not a["resolvido"]),
        },
    }


# ---- Leituras ----
@api_router.get("/leituras", response_model=List[Leitura])
async def list_leituras(propriedade_id: Optional[str] = None, user=Depends(get_current_user)):
    q = scoped_query(user, propriedade_id)
    leituras = await db.leituras.find(q, {"_id": 0}).sort("data_leitura", -1).to_list(None)
    return leituras


@api_router.post("/leituras")
async def create_leitura(
    propriedade_id: str = Form(...),
    leitura_m3: float = Form(..., ge=0, allow_inf_nan=False),
    data_leitura: str = Form(...),
    observacao: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
    user=Depends(get_current_user),
):
    assert_prop_access(user, propriedade_id)
    prop = await _get_prop(propriedade_id)
    try:
        reading_date = datetime.fromisoformat(data_leitura.replace("Z", "+00:00"))
        if reading_date.tzinfo is None:
            reading_date = reading_date.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(422, "Informe uma data válida para a leitura")
    if reading_date > datetime.now(timezone.utc):
        raise HTTPException(422, "A leitura não pode ter uma data futura")
    data_leitura = reading_date.astimezone(timezone.utc).isoformat()
    # calcular consumo com base na leitura anterior
    ult = await db.leituras.find({"propriedade_id": propriedade_id}, {"_id": 0}).sort("data_leitura", -1).to_list(1)
    if ult:
        previous_date = datetime.fromisoformat(ult[0]["data_leitura"].replace("Z", "+00:00"))
        if previous_date.tzinfo is None:
            previous_date = previous_date.replace(tzinfo=timezone.utc)
        if reading_date <= previous_date:
            raise HTTPException(422, "Use uma data posterior à última leitura registrada")
        if leitura_m3 < ult[0]["leitura_m3"]:
            raise HTTPException(422, "O número do hidrômetro não pode ser menor que o da última leitura")
    consumo = leitura_m3 - ult[0]["leitura_m3"] if ult else 0.0
    consumo = max(0.0, consumo)

    foto_path = None
    upload_warning = None
    if foto is not None:
        ext = (foto.filename or "img.jpg").split(".")[-1].lower()
        if ext not in MIME_TYPES:
            ext = "jpg"
        content_type = MIME_TYPES[ext]
        path = f"{APP_NAME}/leituras/{propriedade_id}/{uuid.uuid4()}.{ext}"
        data = await foto.read()
        try:
            result = put_object(path, data, content_type)
            foto_path = result["path"]
            await db.files.insert_one({
                "id": str(uuid.uuid4()),
                "storage_path": foto_path,
                "content_type": content_type,
                "is_deleted": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.error(f"Foto upload failed: {e}")
            upload_warning = "A leitura foi salva, mas a foto não pôde ser anexada. Verifique a configuração de armazenamento."

    leitura = Leitura(
        propriedade_id=propriedade_id,
        leitura_m3=leitura_m3,
        consumo_m3=round(consumo, 2),
        data_leitura=data_leitura,
        observacao=observacao,
        foto_path=foto_path,
    )
    await db.leituras.insert_one(leitura.model_dump())

    # gerar alerta se consumo alto
    baseline = await _baseline_m3(propriedade_id)
    if baseline and consumo > baseline * 1.15:
        alerta = Alerta(
            propriedade_id=propriedade_id,
            tipo="consumo_alto",
            severidade="alta",
            mensagem=f"Consumo {consumo:.1f} m³ está 15% acima da baseline ({baseline:.1f} m³). Verifique vazamento.",
        )
        await db.alertas.insert_one(alerta.model_dump())
    elif baseline and consumo <= baseline * (1 - prop["meta_reducao_pct"] / 100.0):
        alerta = Alerta(
            propriedade_id=propriedade_id,
            tipo="meta_atingida",
            severidade="sucesso",
            mensagem=f"Meta de {prop['meta_reducao_pct']}% atingida no ciclo!",
        )
        await db.alertas.insert_one(alerta.model_dump())

    return {**leitura.model_dump(), "aviso": upload_warning}


@api_router.get("/leituras/foto/{path:path}")
async def download_foto(path: str, user=Depends(get_current_user)):
    leitura = await db.leituras.find_one({"foto_path": path})
    if not leitura:
        raise HTTPException(404, "Foto não encontrada")
    assert_prop_access(user, leitura["propriedade_id"])
    try:
        data, content_type = get_object(path)
        return Response(content=data, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Foto não encontrada: {e}")


# ---- Dejetos ----
@api_router.get("/dejetos", response_model=List[Dejeto])
async def list_dejetos(propriedade_id: Optional[str] = None, user=Depends(get_current_user)):
    q = scoped_query(user, propriedade_id)
    return await db.dejetos.find(q, {"_id": 0}).sort("data_registro", -1).to_list(None)


@api_router.post("/dejetos", response_model=Dejeto)
async def create_dejeto(payload: DejetoCreate, user=Depends(get_current_user)):
    assert_prop_access(user, payload.propriedade_id)
    await _get_prop(payload.propriedade_id)
    biogas = payload.volume_kg * 0.062  # Fator Embrapa Suínos e Aves
    d = Dejeto(
        **payload.model_dump(exclude={"data_registro"}),
        data_registro=payload.data_registro or datetime.now(timezone.utc).isoformat(),
        biogas_m3=round(biogas, 2),
    )
    await db.dejetos.insert_one(d.model_dump())
    return d


# ---- Alertas ----
@api_router.get("/alertas", response_model=List[Alerta])
async def list_alertas(propriedade_id: Optional[str] = None, ativos: bool = False, user=Depends(get_current_user)):
    q = scoped_query(user, propriedade_id)
    if ativos:
        q["resolvido"] = False
    return await db.alertas.find(q, {"_id": 0}).sort("created_at", -1).to_list(None)


@api_router.post("/alertas/{alerta_id}/resolver")
async def resolver_alerta(alerta_id: str, user=Depends(get_current_user)):
    alerta = await db.alertas.find_one({"id": alerta_id})
    if not alerta:
        raise HTTPException(404, "Alerta não encontrado")
    assert_prop_access(user, alerta["propriedade_id"])
    r = await db.alertas.update_one({"id": alerta_id}, {"$set": {"resolvido": True}})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    return {"ok": True}


# ---- Dashboards agregados ----
@api_router.get("/dashboard/frivatti")
async def dashboard_frivatti(user=Depends(require_roles("prefeitura", "frivatti"))):
    props = await db.propriedades.find({}, {"_id": 0}).to_list(None)
    ranking = []
    total_bonus = 0.0
    adesao = 0
    for p in props:
        leituras = await db.leituras.find({"propriedade_id": p["id"]}, {"_id": 0}).sort("data_leitura", 1).to_list(None)
        if not leituras:
            continue
        baseline = await _baseline_m3(p["id"])
        ultimo = leituras[-1]["consumo_m3"]
        economia_pct = ((baseline - ultimo) / baseline * 100) if baseline else 0
        dejetos = await db.dejetos.find({"propriedade_id": p["id"]}, {"_id": 0}).to_list(None)
        biogas_total = sum(d["biogas_m3"] for d in dejetos)
        bonus = max(0, baseline - ultimo) * 12 * 0.35 + biogas_total * 0.8
        total_bonus += bonus
        if p.get("adotou_tecnologia"):
            adesao += 1
        ranking.append({
            "id": p["id"],
            "nome": p["nome"],
            "municipio": p["municipio"],
            "num_suinos": p["num_suinos"],
            "economia_pct": round(economia_pct, 1),
            "biogas_m3": round(biogas_total, 1),
            "bonus_brl": round(bonus, 2),
            "adotou_tecnologia": p.get("adotou_tecnologia", False),
            "tem_biodigestor": p.get("tem_biodigestor", False),
        })
    ranking.sort(key=lambda r: r["economia_pct"], reverse=True)
    return {
        "total_propriedades": len(props),
        "adesao_pct": round(adesao / len(props) * 100, 1) if props else 0,
        "bonus_total_brl": round(total_bonus, 2),
        "ranking": ranking,
    }


@api_router.get("/dashboard/prefeitura")
async def dashboard_prefeitura(user=Depends(require_roles("prefeitura"))):
    props = await db.propriedades.find({}, {"_id": 0}).to_list(None)
    despesas = await db.despesas.find({}, {"_id": 0}).to_list(None)
    gastos = {}
    for despesa in despesas:
        prop_id = despesa["propriedade_id"]
        gastos[prop_id] = gastos.get(prop_id, 0) + despesa["valor_centavos"]
    for prop in props:
        prop["despesas_centavos"] = gastos.get(prop["id"], 0)
    total_consumo = 0.0
    total_baseline_extrapolado = 0.0
    total_biogas = 0.0
    adesao = 0
    municipios = {}
    for p in props:
        leituras = await db.leituras.find({"propriedade_id": p["id"]}, {"_id": 0}).sort("data_leitura", 1).to_list(None)
        baseline = await _baseline_m3(p["id"])
        consumo_p = sum(l["consumo_m3"] for l in leituras)
        total_consumo += consumo_p
        total_baseline_extrapolado += baseline * len(leituras)
        dejetos = await db.dejetos.find({"propriedade_id": p["id"]}, {"_id": 0}).to_list(None)
        total_biogas += sum(d["biogas_m3"] for d in dejetos)
        if p.get("adotou_tecnologia"):
            adesao += 1
        municipios.setdefault(p["municipio"], 0)
        municipios[p["municipio"]] += 1
    economia_m3 = max(0, total_baseline_extrapolado - total_consumo)
    economia_pct = (economia_m3 / total_baseline_extrapolado * 100) if total_baseline_extrapolado else 0
    retorno_econ = economia_m3 * 0.35 + total_biogas * 0.8
    return {
        "total_propriedades": len(props),
        "total_consumo_m3": round(total_consumo, 1),
        "despesas_total_centavos": sum(p["despesas_centavos"] for p in props),
        "economia_m3": round(economia_m3, 1),
        "economia_pct": round(economia_pct, 1),
        "biogas_m3": round(total_biogas, 1),
        "retorno_economico_brl": round(retorno_econ, 2),
        "adesao_pct": round(adesao / len(props) * 100, 1) if props else 0,
        "municipios": [{"municipio": k, "propriedades": v} for k, v in municipios.items()],
        "propriedades": props,
    }


# ---- PDF Relatório ----
@api_router.get("/relatorio/viabilidade")
async def relatorio_viabilidade(user=Depends(require_roles("prefeitura"))):
    dash = await dashboard_prefeitura(user)
    props_ranking = await dashboard_frivatti(user)

    # payback estimation
    capex = 180000.0  # média R$ 180k biodigestor
    retorno_anual = dash["retorno_economico_brl"] * (12 / 10)  # extrapolar 10 meses -> anual
    payback_meses = (capex / (retorno_anual / 12)) if retorno_anual > 0 else 0

    props_detail = []
    for p in dash["propriedades"]:
        leituras = await db.leituras.find({"propriedade_id": p["id"]}, {"_id": 0}).to_list(None)
        consumo_total = sum(l["consumo_m3"] for l in leituras)
        props_detail.append({
            "nome": p["nome"],
            "municipio": p["municipio"],
            "num_suinos": p["num_suinos"],
            "consumo_total_m3": round(consumo_total, 1),
            "meta_reducao_pct": p["meta_reducao_pct"],
            "tem_biodigestor": p["tem_biodigestor"],
        })

    data = {
        "piloto_nome": "AquaSuíno — Piloto 10 Propriedades",
        "municipio": ", ".join(sorted({p["municipio"] for p in dash["propriedades"]})),
        "total_propriedades": dash["total_propriedades"],
        "adesao_pct": dash["adesao_pct"],
        "total_consumo_m3": dash["total_consumo_m3"],
        "total_economia_m3": dash["economia_m3"],
        "economia_pct": dash["economia_pct"],
        "biogas_m3": dash["biogas_m3"],
        "retorno_economico_brl": dash["retorno_economico_brl"],
        "capex_estimado": capex,
        "payback_meses": round(payback_meses, 1),
        "propriedades": props_detail,
    }
    pdf_bytes = build_viability_pdf(data)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="aquasuino_viabilidade.pdf"'},
    )


def scoped_query(user, prop_id=None):
    if prop_id:
        assert_prop_access(user, prop_id)
    if user["role"] == "produtor":
        return {"propriedade_id": user.get("propriedade_id") or "__unassigned__"}
    return {"propriedade_id": prop_id} if prop_id else {}


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserInput(LoginInput):
    nome: str = Field(min_length=2, max_length=120)
    propriedade_id: str


class CadastroInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=72)
    fazenda: str = Field(min_length=2, max_length=120)
    municipio: str = Field(min_length=2, max_length=120)
    num_suinos: int = Field(ge=0, le=1000000)
    area_m2: float = Field(gt=0, le=1000000000, allow_inf_nan=False)
    fonte_agua: str = Field(min_length=2, max_length=120)
    hidrometro_serial: str = Field(min_length=1, max_length=120)

    @field_validator("nome", "fazenda", "municipio", "fonte_agua", "hidrometro_serial", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


@api_router.post("/auth/cadastro", status_code=201)
async def cadastro(payload: CadastroInput, request: Request):
    identifier = "cadastro:" + (request.client.host if request.client else "unknown")
    await check_lockout(identifier)
    await register_failure(identifier)  # At most five registrations per IP in 15 minutes.
    if len(payload.password.encode("utf-8")) > 72:
        raise HTTPException(422, "A senha deve ter no máximo 72 bytes")
    email = str(payload.email).lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(409, "Este e-mail já possui uma conta. Entre ou recupere seu acesso.")
    prop = Propriedade(nome=payload.fazenda, municipio=payload.municipio,
        produtor_nome=payload.nome, num_suinos=payload.num_suinos, area_m2=payload.area_m2,
        fonte_agua=payload.fonte_agua, hidrometro_serial=payload.hidrometro_serial)
    user = {"id": str(uuid.uuid4()), "email": email, "nome": payload.nome,
            "role": "produtor", "propriedade_id": prop.id, "ativo": False,
            "password_hash": hash_password(payload.password),
            "created_at": datetime.now(timezone.utc).isoformat()}
    try:
        await db.users.insert_one(dict(user))
    except DuplicateKeyError:
        raise HTTPException(409, "Este e-mail já possui uma conta. Entre ou recupere seu acesso.")
    try:
        await db.propriedades.insert_one(prop.model_dump())
        await db.users.update_one({"id": user["id"]}, {"$set": {"ativo": True}})
    except Exception:
        await db.users.delete_one({"id": user["id"]})
        await db.propriedades.delete_one({"id": prop.id})
        raise HTTPException(503, "Não foi possível concluir o cadastro. Tente novamente.")
    user["ativo"] = True
    return public_user(user)


@api_router.post("/auth/login")
async def login(payload: LoginInput, response: Response):
    email = str(payload.email).strip().lower()
    await check_lockout(email)
    user = await db.users.find_one({"email": email})
    if not user or not user.get("ativo", True) or not verify_password(payload.password, user["password_hash"]):
        await register_failure(email)
        raise HTTPException(401, "E-mail ou senha incorretos")
    await clear_failures(email)
    response.set_cookie("access_token", create_access_token(user), httponly=True,
                        secure=os.environ.get("COOKIE_SECURE", "true").lower() == "true",
                        samesite="lax", max_age=43200, path="/api")
    return public_user(user)


@api_router.get("/auth/me")
async def me(user=Depends(get_current_user)):
    return public_user(user)


@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/api")
    return {"ok": True}


@api_router.post("/usuarios", status_code=201)
async def create_user(payload: UserInput, user=Depends(require_roles("prefeitura"))):
    await _get_prop(payload.propriedade_id)
    if len(payload.password) < 10 or len(payload.password.encode("utf-8")) > 72:
        raise HTTPException(422, "Use uma senha com pelo menos 10 caracteres e até 72 bytes")
    doc = {"id": str(uuid.uuid4()), "email": str(payload.email).lower().strip(),
           "nome": payload.nome, "role": "produtor", "propriedade_id": payload.propriedade_id,
           "password_hash": hash_password(payload.password)}
    try:
        await db.users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "Este e-mail já está cadastrado")
    return public_user(doc)


class DespesaInput(BaseModel):
    propriedade_id: str
    descricao: str = Field(min_length=2, max_length=200)
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    data: date


@api_router.get("/despesas")
async def list_despesas(propriedade_id: Optional[str] = None, user=Depends(get_current_user)):
    return await db.despesas.find(scoped_query(user, propriedade_id), {"_id": 0}).sort("data", -1).to_list(None)


@api_router.post("/despesas", status_code=201)
async def create_despesa(payload: DespesaInput, user=Depends(get_current_user)):
    assert_prop_access(user, payload.propriedade_id)
    await _get_prop(payload.propriedade_id)
    doc = {"id": str(uuid.uuid4()), "propriedade_id": payload.propriedade_id,
           "descricao": payload.descricao, "valor_centavos": int(payload.valor * 100),
           "data": payload.data.isoformat(), "criado_por": user["id"]}
    await db.despesas.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.delete("/despesas/{despesa_id}")
async def delete_despesa(despesa_id: str, user=Depends(get_current_user)):
    expense = await db.despesas.find_one({"id": despesa_id})
    if not expense:
        raise HTTPException(404, "Despesa não encontrada")
    assert_prop_access(user, expense["propriedade_id"])
    await db.despesas.delete_one({"id": despesa_id, "propriedade_id": expense["propriedade_id"]})
    return {"ok": True}


@app.middleware("http")
async def protect_cookie_writes(request: Request, call_next):
    # Custom header prevents cross-site form submissions; CORS permits trusted origins only.
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/api/"):
        if request.headers.get("X-Requested-With") != "AquaSuino":
            return Response(status_code=403)
    return await call_next(request)


from management import register_management
register_management(api_router, lambda: db, get_propriedade)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

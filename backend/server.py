"""AquaSuíno backend — hydric + waste management for swine farms."""
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form, Response, Depends, Request
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from pathlib import Path
from datetime import datetime, timezone
from io import BytesIO
import os
import uuid
import logging

from storage import init_storage, put_object, get_object, MIME_TYPES, APP_NAME
from pdf_report import build_viability_pdf


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

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
async def list_propriedades():
    props = await db.propriedades.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return props


@api_router.post("/propriedades", response_model=Propriedade)
async def create_propriedade(payload: PropriedadeCreate):
    prop = Propriedade(**payload.model_dump())
    await db.propriedades.insert_one(prop.model_dump())
    return prop


@api_router.get("/propriedades/{prop_id}")
async def get_propriedade(prop_id: str):
    prop = await _get_prop(prop_id)
    leituras = await db.leituras.find({"propriedade_id": prop_id}, {"_id": 0}).sort("data_leitura", 1).to_list(500)
    dejetos = await db.dejetos.find({"propriedade_id": prop_id}, {"_id": 0}).sort("data_registro", 1).to_list(500)
    alertas = await db.alertas.find({"propriedade_id": prop_id}, {"_id": 0}).sort("created_at", -1).to_list(200)
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
async def list_leituras(propriedade_id: Optional[str] = None):
    q = {"propriedade_id": propriedade_id} if propriedade_id else {}
    leituras = await db.leituras.find(q, {"_id": 0}).sort("data_leitura", -1).to_list(500)
    return leituras


@api_router.post("/leituras")
async def create_leitura(
    propriedade_id: str = Form(...),
    leitura_m3: float = Form(...),
    data_leitura: str = Form(...),
    observacao: Optional[str] = Form(None),
    foto: Optional[UploadFile] = File(None),
):
    prop = await _get_prop(propriedade_id)
    # calcular consumo com base na leitura anterior
    ult = await db.leituras.find({"propriedade_id": propriedade_id}, {"_id": 0}).sort("data_leitura", -1).to_list(1)
    consumo = leitura_m3 - ult[0]["leitura_m3"] if ult else 0.0
    consumo = max(0.0, consumo)

    foto_path = None
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

    return leitura


@api_router.get("/leituras/foto/{path:path}")
async def download_foto(path: str):
    try:
        data, content_type = get_object(path)
        return Response(content=data, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Foto não encontrada: {e}")


# ---- Dejetos ----
@api_router.get("/dejetos", response_model=List[Dejeto])
async def list_dejetos(propriedade_id: Optional[str] = None):
    q = {"propriedade_id": propriedade_id} if propriedade_id else {}
    return await db.dejetos.find(q, {"_id": 0}).sort("data_registro", -1).to_list(500)


@api_router.post("/dejetos", response_model=Dejeto)
async def create_dejeto(payload: DejetoCreate):
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
async def list_alertas(propriedade_id: Optional[str] = None, ativos: bool = False):
    q = {}
    if propriedade_id:
        q["propriedade_id"] = propriedade_id
    if ativos:
        q["resolvido"] = False
    return await db.alertas.find(q, {"_id": 0}).sort("created_at", -1).to_list(200)


@api_router.post("/alertas/{alerta_id}/resolver")
async def resolver_alerta(alerta_id: str):
    r = await db.alertas.update_one({"id": alerta_id}, {"$set": {"resolvido": True}})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    return {"ok": True}


# ---- Dashboards agregados ----
@api_router.get("/dashboard/frivatti")
async def dashboard_frivatti():
    props = await db.propriedades.find({}, {"_id": 0}).to_list(200)
    ranking = []
    total_bonus = 0.0
    adesao = 0
    for p in props:
        leituras = await db.leituras.find({"propriedade_id": p["id"]}, {"_id": 0}).sort("data_leitura", 1).to_list(500)
        if not leituras:
            continue
        baseline = await _baseline_m3(p["id"])
        ultimo = leituras[-1]["consumo_m3"]
        economia_pct = ((baseline - ultimo) / baseline * 100) if baseline else 0
        dejetos = await db.dejetos.find({"propriedade_id": p["id"]}, {"_id": 0}).to_list(500)
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
async def dashboard_prefeitura():
    props = await db.propriedades.find({}, {"_id": 0}).to_list(200)
    total_consumo = 0.0
    total_baseline_extrapolado = 0.0
    total_biogas = 0.0
    adesao = 0
    municipios = {}
    for p in props:
        leituras = await db.leituras.find({"propriedade_id": p["id"]}, {"_id": 0}).sort("data_leitura", 1).to_list(500)
        baseline = await _baseline_m3(p["id"])
        consumo_p = sum(l["consumo_m3"] for l in leituras)
        total_consumo += consumo_p
        total_baseline_extrapolado += baseline * len(leituras)
        dejetos = await db.dejetos.find({"propriedade_id": p["id"]}, {"_id": 0}).to_list(500)
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
async def relatorio_viabilidade():
    dash = await dashboard_prefeitura()
    props_ranking = await dashboard_frivatti()

    # payback estimation
    capex = 180000.0  # média R$ 180k biodigestor
    retorno_anual = dash["retorno_economico_brl"] * (12 / 10)  # extrapolar 10 meses -> anual
    payback_meses = (capex / (retorno_anual / 12)) if retorno_anual > 0 else 0

    props_detail = []
    for p in dash["propriedades"]:
        leituras = await db.leituras.find({"propriedade_id": p["id"]}, {"_id": 0}).to_list(500)
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


# ---- Seed endpoint (idempotent trigger) ----
@api_router.post("/seed")
async def trigger_seed():
    from seed import seed as run_seed
    await run_seed()
    return {"ok": True}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

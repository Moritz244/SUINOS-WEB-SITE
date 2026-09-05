"""Seed 10 propriedades and 10 months of readings for the AquaSuíno demo."""
import asyncio
import os
import uuid
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

MUNICIPIO_DEFAULT = "Itapiranga/SC"

PRODUTORES = [
    ("Granja Vale Verde", "Itapiranga/SC", 1200, 4800, True),
    ("Sítio Rio Uruguai", "Itapiranga/SC", 800, 3200, True),
    ("Fazenda Boa Vista", "Itapiranga/SC", 1500, 6000, True),
    ("Granja Água Limpa", "Mondaí/SC", 900, 3600, False),
    ("Sítio Colina Alta", "Itapiranga/SC", 600, 2400, False),
    ("Fazenda Três Pinheiros", "São João do Oeste/SC", 1100, 4400, True),
    ("Granja Nova Aliança", "Itapiranga/SC", 700, 2800, False),
    ("Sítio Recanto Verde", "Mondaí/SC", 1000, 4000, True),
    ("Fazenda Pôr do Sol", "Tunápolis/SC", 850, 3400, False),
    ("Granja Serra Azul", "Itapiranga/SC", 1300, 5200, True),
]


async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    await db.propriedades.delete_many({})
    await db.leituras.delete_many({})
    await db.alertas.delete_many({})
    await db.dejetos.delete_many({})

    now = datetime.now(timezone.utc)
    random.seed(42)

    for i, (nome, municipio, num_suinos, area_m2, tem_bio) in enumerate(PRODUTORES):
        prop_id = str(uuid.uuid4())
        adotou_tech = i < 6  # 6/10 adhered
        prop = {
            "id": prop_id,
            "nome": nome,
            "municipio": municipio,
            "produtor_nome": f"Produtor {i+1}",
            "num_suinos": num_suinos,
            "area_m2": area_m2,
            "fonte_agua": random.choice(["poço artesiano", "rio", "rede pública"]),
            "tem_biodigestor": tem_bio,
            "adotou_tecnologia": adotou_tech,  # gotejamento/nebulização
            "hidrometro_serial": f"HID-{2024000 + i}",
            "meta_reducao_pct": 10,
            "created_at": (now - timedelta(days=310)).isoformat(),
        }
        await db.propriedades.insert_one(prop)

        # Baseline: ~5L per suíno per dia (Embrapa reference); vary per property
        base_daily_per_pig = 4.5 + random.uniform(-0.3, 0.8)
        baseline_monthly_m3 = (base_daily_per_pig * num_suinos * 30) / 1000.0

        prev_reading = 1000.0 + random.uniform(0, 500)
        for m in range(10):
            month_date = now - timedelta(days=(9 - m) * 30)
            # Adopters progressively reduce consumption
            reduction = 0.0
            if adotou_tech and m >= 2:
                reduction = min(0.12, (m - 1) * 0.02)
            noise = random.uniform(-0.05, 0.05)
            consumo = baseline_monthly_m3 * (1 - reduction + noise)
            new_reading = prev_reading + consumo
            leitura = {
                "id": str(uuid.uuid4()),
                "propriedade_id": prop_id,
                "leitura_m3": round(new_reading, 2),
                "consumo_m3": round(consumo, 2),
                "data_leitura": month_date.isoformat(),
                "foto_path": None,
                "observacao": "Leitura mensal manual",
                "created_at": month_date.isoformat(),
            }
            await db.leituras.insert_one(leitura)
            prev_reading = new_reading

            # dejetos + biogás
            if tem_bio:
                # ~7 kg dejeto/suíno/dia; fator Embrapa ~0.062 m³ biogás/kg
                dejetos_kg = 7 * num_suinos * 30 * random.uniform(0.9, 1.05)
                biogas_m3 = dejetos_kg * 0.062
                await db.dejetos.insert_one({
                    "id": str(uuid.uuid4()),
                    "propriedade_id": prop_id,
                    "volume_kg": round(dejetos_kg, 1),
                    "biogas_m3": round(biogas_m3, 1),
                    "destino_digestato": random.choice(["fertirrigação", "lavoura milho", "pastagem"]),
                    "destino_agua_tratada": "reúso na granja (limpeza baias)",
                    "conforme_conama": True,
                    "data_registro": month_date.isoformat(),
                    "created_at": month_date.isoformat(),
                })

            # Alertas: se consumo > baseline*1.08 -> alerta
            if consumo > baseline_monthly_m3 * 1.08:
                await db.alertas.insert_one({
                    "id": str(uuid.uuid4()),
                    "propriedade_id": prop_id,
                    "tipo": "consumo_alto",
                    "severidade": "media",
                    "mensagem": f"Consumo {consumo:.1f} m³ acima da média histórica — verificar vazamento.",
                    "resolvido": m < 8,
                    "created_at": month_date.isoformat(),
                })

        # Meta atingida no último mês pra quem adotou
        if adotou_tech:
            await db.alertas.insert_one({
                "id": str(uuid.uuid4()),
                "propriedade_id": prop_id,
                "tipo": "meta_atingida",
                "severidade": "sucesso",
                "mensagem": "Meta de 10% de redução atingida no último ciclo.",
                "resolvido": False,
                "created_at": now.isoformat(),
            })

    print(f"Seeded {len(PRODUTORES)} propriedades, 10 meses cada.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())

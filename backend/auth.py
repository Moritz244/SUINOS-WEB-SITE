"""JWT auth helpers — email/senha com bcrypt, 3 roles."""
import os
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from fastapi import Request, HTTPException, Depends

JWT_ALGORITHM = "HS256"
ROLES = ("produtor", "frivatti", "prefeitura")
_db = None


def bind_db(db):
    global _db
    _db = db


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user: dict) -> str:
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
        "type": "access",
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm=JWT_ALGORITHM)


def public_user(user: dict) -> dict:
    return {k: v for k, v in user.items() if k not in ("_id", "password_hash")}


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sessão expirada")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token inválido")
    user = await _db.users.find_one({"id": payload["sub"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user


def require_roles(*roles):
    async def dep(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Acesso negado para este perfil")
        return user
    return dep


def assert_prop_access(user: dict, prop_id: str):
    if user["role"] == "produtor" and user.get("propriedade_id") != prop_id:
        raise HTTPException(status_code=403, detail="Você só pode acessar a sua propriedade")


async def check_lockout(identifier: str):
    doc = await _db.login_attempts.find_one({"identifier": identifier})
    if doc and doc.get("count", 0) >= 5:
        locked_until = datetime.fromisoformat(doc["locked_until"])
        if datetime.now(timezone.utc) < locked_until:
            raise HTTPException(status_code=429, detail="Muitas tentativas. Tente novamente em 15 minutos.")
        await _db.login_attempts.delete_one({"identifier": identifier})


async def register_failure(identifier: str):
    await _db.login_attempts.update_one(
        {"identifier": identifier},
        {"$inc": {"count": 1}, "$set": {"locked_until": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()}},
        upsert=True,
    )


async def clear_failures(identifier: str):
    await _db.login_attempts.delete_one({"identifier": identifier})


async def upsert_user(email: str, password: str, nome: str, role: str, propriedade_id=None) -> dict:
    email = email.lower().strip()
    existing = await _db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        updates = {"nome": nome, "role": role, "propriedade_id": propriedade_id}
        if not verify_password(password, existing["password_hash"]):
            updates["password_hash"] = hash_password(password)
        await _db.users.update_one({"email": email}, {"$set": updates})
        return {**existing, **updates}
    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": hash_password(password),
        "nome": nome,
        "role": role,
        "propriedade_id": propriedade_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await _db.users.insert_one(dict(user))
    return user


async def seed_users(props: list):
    """Admin (prefeitura), Frivatti e 1 produtor por propriedade."""
    await _db.users.create_index("email", unique=True)
    await _db.login_attempts.create_index("identifier")
    demo_pw = os.environ["DEMO_PASSWORD"]
    await upsert_user(os.environ["ADMIN_EMAIL"], os.environ["ADMIN_PASSWORD"], "Administrador", "prefeitura")
    await upsert_user("prefeitura@aquasuino.com", demo_pw, "Secretaria de Agricultura", "prefeitura")
    await upsert_user("frivatti@aquasuino.com", demo_pw, "Frivatti Agroindustrial", "frivatti")
    for i, p in enumerate(props):
        await upsert_user(f"produtor{i+1}@aquasuino.com", demo_pw, p["produtor_nome"], "produtor", p["id"])

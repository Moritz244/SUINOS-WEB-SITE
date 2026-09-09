"""Create the first prefeitura account without modifying existing users."""
import asyncio
import getpass
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import TypeAdapter, EmailStr
from auth import hash_password

async def main():
    load_dotenv(Path(__file__).parent / ".env.local")
    load_dotenv(Path(__file__).parent / ".env")
    email = str(TypeAdapter(EmailStr).validate_python(input("E-mail da prefeitura: ").strip())).lower()
    nome = input("Nome: ").strip()
    password = getpass.getpass("Senha (mínimo 10 caracteres): ")
    if not nome or len(password) < 10 or len(password.encode("utf-8")) > 72:
        raise SystemExit("Informe nome e senha válidos (máximo 72 bytes).")
    if password != getpass.getpass("Confirme a senha: "):
        raise SystemExit("As senhas não coincidem.")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    try:
        db = client[os.environ["DB_NAME"]]
        await db.users.create_index("email", unique=True)
        if await db.users.find_one({"email": email}):
            raise SystemExit("Este e-mail já existe. Nenhuma conta foi alterada.")
        await db.users.insert_one({"id": str(uuid.uuid4()), "email": email, "nome": nome,
                                   "role": "prefeitura", "password_hash": hash_password(password)})
        print("Conta da prefeitura criada.")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())

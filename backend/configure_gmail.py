"""Run locally in a terminal to configure Gmail without putting secrets in chat."""
import getpass
from pathlib import Path
from dotenv import set_key
from pydantic import TypeAdapter, EmailStr

def main():
    print("Configure uma conta Gmail com verificação em duas etapas e uma senha de app.")
    email = str(TypeAdapter(EmailStr).validate_python(input("Gmail remetente: ").strip()))
    password = getpass.getpass("Senha de app do Google (entrada oculta): ").replace(" ", "")
    if not password or "\n" in password or "\r" in password:
        raise SystemExit("Senha de app não informada ou inválida.")
    url = input("Endereço do site [http://127.0.0.1:8765]: ").strip() or "http://127.0.0.1:8765"
    settings = {"SMTP_HOST":"smtp.gmail.com", "SMTP_PORT":"587", "SMTP_SECURITY":"starttls",
                "SMTP_FROM":email, "SMTP_USERNAME":email, "SMTP_PASSWORD":password, "PUBLIC_APP_URL":url}
    path = Path(__file__).parent / ".env.local"
    path.touch(exist_ok=True)
    for key, value in settings.items():
        set_key(str(path), key, value)
    print("Configuração salva em .env.local. Reinicie a API para ativar o envio.")
    print("Em outro dispositivo, um link de localhost não abrirá este computador. Para uso público, configure o domínio HTTPS do site.")

if __name__ == "__main__":
    main()

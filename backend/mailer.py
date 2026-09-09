"""Transactional recovery emails. Credentials come only from the environment."""
import os
import ssl
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from urllib.parse import urlsplit

def mail_settings():
    host = os.environ.get("SMTP_HOST", "").strip()
    sender = os.environ.get("SMTP_FROM", "").strip()
    base = os.environ.get("PUBLIC_APP_URL", "").rstrip("/")
    url = urlsplit(base)
    local = url.hostname in {"localhost", "127.0.0.1", "::1"}
    if not host or not sender or "@" not in sender or "\n" in sender or "\r" in sender:
        raise ValueError("Configure SMTP_HOST e SMTP_FROM")
    if url.scheme != "https" and not (local and url.scheme == "http"):
        raise ValueError("Configure PUBLIC_APP_URL com HTTPS (HTTP permitido apenas localmente)")
    if not url.netloc or url.username or url.password or url.query or url.fragment:
        raise ValueError("PUBLIC_APP_URL inválida")
    mode = os.environ.get("SMTP_SECURITY", "starttls")
    if mode not in {"starttls", "ssl"}:
        raise ValueError("SMTP_SECURITY deve ser starttls ou ssl")
    return {"host": host, "sender": sender, "base": base, "mode": mode,
            "port": int(os.environ.get("SMTP_PORT", "465" if mode == "ssl" else "587")),
            "username": os.environ.get("SMTP_USERNAME", ""), "password": os.environ.get("SMTP_PASSWORD", "")}

def recovery_content(name, url):
    raw_name = name or ""
    name, link = escape(raw_name), escape(url, quote=True)
    text = f"Olá, {name}!\n\nRecebemos um pedido para redefinir sua senha no AquaSuíno.\n\nCrie uma nova senha pelo link:\n{url}\n\nEste link é válido por 30 minutos e só pode ser usado uma vez.\nSe você não fez este pedido, ignore esta mensagem. Sua senha permanece a mesma.\nNunca compartilhe sua senha ou este link.\n\nEquipe AquaSuíno\nCuidado com a água. Gestão para sua fazenda."
    text = text.replace(name, raw_name, 1) if name else text
    html = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Redefina sua senha | AquaSuíno</title></head>
<body style="margin:0;padding:0;background:#f1f5f4;font-family:Arial,Helvetica,sans-serif;color:#12372c;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">Seu próximo acesso começa aqui. Redefina sua senha com segurança em até 30 minutos.</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f5f4;"><tr><td align="center" style="padding:32px 16px;">
<table role="presentation" width="600" cellspacing="0" cellpadding="0" style="width:100%;max-width:600px;">
<tr><td style="padding:0 0 24px;font-size:25px;font-weight:bold;letter-spacing:-1px;text-align:center;color:#087f5b;">AquaSuíno</td></tr>
<tr><td style="background:#073f33;border-radius:20px 20px 0 0;padding:36px 32px;">
<p style="margin:0 0 14px;color:#9fe8c9;font-size:11px;font-weight:bold;letter-spacing:2px;">SEGURANÇA DA SUA CONTA</p>
<h1 style="margin:0;color:#ffffff;font-size:32px;line-height:1.2;letter-spacing:-1px;">Um novo acesso.<br>O mesmo cuidado.</h1>
<p style="margin:16px 0 0;color:#c7e5da;font-size:15px;line-height:1.6;">Vamos ajudar você a voltar para o que importa.</p>
</td></tr>
<tr><td style="background:#fff;padding:32px;border-radius:0 0 20px 20px;">
<p style="margin:0 0 16px;font-size:18px;font-weight:bold;line-height:1.5;">Olá, {name}!</p>
<p style="margin:0 0 24px;color:#52645e;font-size:16px;line-height:1.7;">Recebemos um pedido para redefinir a senha da sua conta no <strong>AquaSuíno</strong>. Toque no botão abaixo para escolher uma nova senha e continuar acompanhando sua fazenda.</p>
<table role="presentation" cellspacing="0" cellpadding="0"><tr><td bgcolor="#059669" style="border-radius:10px;text-align:center;"><a href="{link}" style="display:inline-block;padding:17px 28px;border:1px solid #059669;border-radius:10px;color:#fff;font-size:16px;font-weight:bold;text-decoration:none;">Redefinir minha senha</a></td></tr></table>
<p style="margin:20px 0 28px;color:#63776e;font-size:13px;line-height:1.6;">Válido por <strong>30 minutos</strong> · Uso único</p>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr><td style="background:#ecf8f1;border-left:3px solid #059669;padding:18px 20px;border-radius:4px;">
<p style="margin:0 0 6px;font-size:14px;font-weight:bold;">Não foi você quem pediu?</p><p style="margin:0;color:#52645e;font-size:13px;line-height:1.7;">Pode ignorar este e-mail. Sua senha continua a mesma e nenhuma alteração será feita sem sua confirmação.</p></td></tr></table>
<p style="margin:28px 0 8px;color:#63776e;font-size:12px;line-height:1.6;">Se o botão não funcionar, copie e cole este endereço no navegador:</p>
<p style="margin:0;font-size:12px;line-height:1.7;word-break:break-all;overflow-wrap:anywhere;"><a href="{link}" style="color:#087f5b;text-decoration:underline;word-break:break-all;">{link}</a></p>
</td></tr>
<tr><td style="padding:24px 20px 0;text-align:center;color:#6a7b73;font-size:12px;line-height:1.8;">Nunca compartilhe sua senha ou este link.<br><strong style="color:#395a4b;">Equipe AquaSuíno</strong><br>Cuidado com a água. Gestão para sua fazenda.</td></tr>
</table></td></tr></table></body></html>'''
    return text, html

def send_recovery_email(recipient, name, token):
    config = mail_settings()
    text, html = recovery_content(name, config["base"] + "/recuperar#token=" + token)
    message = EmailMessage()
    message["Subject"] = "Vamos recuperar seu acesso ao AquaSuíno?"
    message["From"] = formataddr(("AquaSuíno", config["sender"]))
    message["To"] = recipient
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    context = ssl.create_default_context()
    if config["mode"] == "ssl":
        connection = smtplib.SMTP_SSL(config["host"], config["port"], timeout=20, context=context)
    else:
        connection = smtplib.SMTP(config["host"], config["port"], timeout=20)
    with connection as smtp:
        if config["mode"] == "starttls":
            smtp.ehlo(); smtp.starttls(context=context); smtp.ehlo()
        if config["username"]:
            smtp.login(config["username"], config["password"])
        refused = smtp.send_message(message)
        if refused:
            raise RuntimeError("Destinatário recusado pelo servidor SMTP")

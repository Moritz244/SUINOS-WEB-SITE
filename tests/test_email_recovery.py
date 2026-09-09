from .test_access import db, request
from unittest.mock import Mock, MagicMock
import pytest
import management
import mailer

@pytest.fixture
def configured(monkeypatch):
    for key,value in {"SMTP_HOST":"smtp.gmail.com","SMTP_PORT":"587","SMTP_FROM":"sender@example.com","SMTP_USERNAME":"sender@example.com","SMTP_PASSWORD":"test-app-password","SMTP_SECURITY":"starttls","PUBLIC_APP_URL":"https://aquasuino.example"}.items():
        monkeypatch.setenv(key,value)

def test_unknown_and_known_have_same_response_and_token_not_exposed(db,configured,monkeypatch):
    sender=Mock(); monkeypatch.setattr(management,"send_recovery_email",sender)
    known=request("POST","/auth/esqueci-senha",json={"email":"a@example.com"})
    unknown=request("POST","/auth/esqueci-senha",json={"email":"unknown@example.com"})
    assert known.status_code==unknown.status_code==202 and known.json()==unknown.json()=={"ok":True}
    sender.assert_called_once()
    recipient,name,token=sender.call_args.args
    assert recipient=="a@example.com" and token not in known.text
    assert request("POST","/auth/redefinir-senha",json={"token":token,"nova":"email-new-password"}).status_code==200
    assert request("POST","/auth/redefinir-senha",json={"token":token,"nova":"email-new-password"}).status_code==400

def test_disabled_account_receives_nothing(db,configured,monkeypatch):
    db.users.rows[0]["ativo"]=False
    sender=Mock();monkeypatch.setattr(management,"send_recovery_email",sender)
    assert request("POST","/auth/esqueci-senha",json={"email":"a@example.com"}).status_code==202
    sender.assert_not_called()

def test_missing_configuration_is_not_fake_delivery(db,monkeypatch):
    monkeypatch.delenv("SMTP_HOST",raising=False)
    assert request("POST","/auth/esqueci-senha",json={"email":"a@example.com"}).status_code==503

def test_failed_delivery_invalidates_token(db,configured,monkeypatch):
    monkeypatch.setattr(management,"send_recovery_email",Mock(side_effect=OSError("smtp unavailable")))
    assert request("POST","/auth/esqueci-senha",json={"email":"a@example.com"}).status_code==202
    assert db.users.rows[0]["reset_hash"] is None

def test_smtp_tls_and_multipart(configured,monkeypatch):
    connection=MagicMock();connection.__enter__.return_value=connection;connection.send_message.return_value={}
    factory=Mock(return_value=connection);monkeypatch.setattr(mailer.smtplib,"SMTP",factory)
    mailer.send_recovery_email("a@example.com","Ana <teste>","safe-token")
    connection.starttls.assert_called_once();connection.login.assert_called_once_with("sender@example.com","test-app-password")
    message=connection.send_message.call_args.args[0]
    assert message["To"]=="a@example.com"
    assert message.get_body(preferencelist=("plain",)).get_content().startswith("Olá, Ana <teste>!")
    html=message.get_body(preferencelist=("html",)).get_content()
    assert "Ana &lt;teste&gt;" in html and "https://aquasuino.example/recuperar#token=safe-token" in html

def test_email_request_rate_limit(db,configured,monkeypatch):
    monkeypatch.setattr(management,"send_recovery_email",Mock())
    for _ in range(5): assert request("POST","/auth/esqueci-senha",json={"email":"unknown@example.com"}).status_code==202
    assert request("POST","/auth/esqueci-senha",json={"email":"unknown@example.com"}).status_code==429

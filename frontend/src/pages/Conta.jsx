import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import RecuperarEmail from "../components/RecuperarEmail";
export default function Conta({ recovery = false }) {
  const { endSession } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [done, setDone] = useState(false);
  const [token] = useState(() => new URLSearchParams(window.location.hash.slice(1)).get("token") || "");
  if (recovery && !token && !done) return <RecuperarEmail />;
  async function submit(e) {
    e.preventDefault(); const data = Object.fromEntries(new FormData(e.currentTarget));
    if (data.nova !== data.confirmacao) { setMessage("As senhas não coincidem."); return; }
    setBusy(true); setMessage("");
    try {
      await api.post(recovery ? "/auth/redefinir-senha" : "/auth/senha", recovery ? { token, nova: data.nova } : { atual: data.atual, nova: data.nova });
      endSession(); setDone(true); window.history.replaceState(null, "", window.location.pathname);
    } catch (err) { setMessage(typeof err.response?.data?.detail === "string" ? err.response.data.detail : "Não foi possível alterar a senha. Verifique os dados."); }
    finally { setBusy(false); }
  }
  return <main className="max-w-lg mx-auto px-4 py-12"><section className="bg-white border rounded-2xl p-7">
    <h1 className="text-2xl font-bold mb-3">{recovery ? "Recuperar acesso" : "Minha conta"}</h1>
    {done ? <div><p role="status">Senha alterada. As sessões anteriores foram encerradas.</p><Button className="mt-4" onClick={() => navigate("/login")}>Entrar novamente</Button></div> : recovery && !token ? <p>Solicite um link de recuperação à prefeitura. Ele é válido por 30 minutos e pode ser usado uma única vez.</p> : <form onSubmit={submit} className="space-y-4">
      <p className="text-sm text-slate-500">Use pelo menos 10 caracteres. Após a alteração, entre novamente com a nova senha.</p>
      {!recovery && <div><Label htmlFor="atual">Senha atual</Label><Input id="atual" name="atual" type="password" autoComplete="current-password" required /></div>}
      <div><Label htmlFor="nova">Nova senha</Label><Input id="nova" name="nova" type="password" minLength={10} maxLength={72} autoComplete="new-password" required /></div>
      <div><Label htmlFor="confirmacao">Confirmar nova senha</Label><Input id="confirmacao" name="confirmacao" type="password" minLength={10} maxLength={72} autoComplete="new-password" required /></div>
      {message && <p className="text-red-700" role="alert">{message}</p>}
      <Button disabled={busy}>{busy ? "Salvando…" : "Alterar senha"}</Button>
    </form>}
  </section></main>;
}

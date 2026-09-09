import { useState } from "react";
import { Link } from "react-router-dom";
import { Mail, ArrowLeft, ShieldCheck, CheckCircle2 } from "lucide-react";
import { api } from "../lib/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
export default function RecuperarEmail() {
  const [busy,setBusy]=useState(false), [done,setDone]=useState(false), [error,setError]=useState("");
  async function submit(e) {
    e.preventDefault(); setBusy(true); setError("");
    const email = new FormData(e.currentTarget).get("email");
    try { await api.post("/auth/esqueci-senha",{email}); setDone(true); }
    catch(e) { setError(typeof e.response?.data?.detail === "string" ? e.response.data.detail : "Não foi possível solicitar o e-mail. Tente novamente."); }
    finally { setBusy(false); }
  }
  return <main className="max-w-lg mx-auto px-4 py-12 sm:py-20"><section className="bg-white border border-emerald-100 rounded-3xl overflow-hidden shadow-sm">
    <div className="bg-[#073f33] text-white px-7 py-9"><div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center mb-5">{done ? <CheckCircle2 className="text-emerald-200"/> : <Mail className="text-emerald-200"/>}</div><p className="text-emerald-200 text-xs font-semibold uppercase tracking-widest mb-3">Acesso com segurança</p><h1 className="text-3xl font-bold tracking-tight">{done ? "Confira seu e-mail" : "Esqueceu sua senha?"}</h1><p className="text-emerald-100/80 mt-3 leading-relaxed">{done ? "Você está a um passo de voltar." : "Vamos ajudar você a voltar para o que importa."}</p></div>
    <div className="p-7">{done ? <div role="status"><p className="text-slate-600 leading-relaxed">Se este e-mail estiver vinculado a uma conta ativa, você receberá um link para criar uma nova senha.</p><p className="text-sm text-slate-500 mt-4">O link vale por 30 minutos. Confira também as pastas de spam e lixo eletrônico.</p><Button variant="outline" className="mt-6 w-full" onClick={()=>setDone(false)}>Tentar outro e-mail</Button></div> : <form onSubmit={submit} className="space-y-5"><div><Label htmlFor="recovery-email">E-mail da sua conta</Label><Input id="recovery-email" name="email" type="email" autoComplete="email" placeholder="voce@exemplo.com" required className="mt-2 h-12"/></div>{error && <p role="alert" className="text-red-700 text-sm">{error}</p>}<Button className="w-full h-12 btn-primary" disabled={busy}>{busy ? "Solicitando…" : "Enviar link de recuperação"}</Button></form>}
    <div className="bg-emerald-50 rounded-xl p-4 flex gap-3 mt-6 text-sm text-emerald-900"><ShieldCheck className="w-5 h-5 shrink-0 mt-0.5"/><p>O link é de uso único. Sua senha só muda quando você escolher uma nova.</p></div><Link to="/login" className="flex justify-center items-center gap-2 mt-6 text-sm font-semibold text-emerald-700"><ArrowLeft className="w-4 h-4"/>Voltar para entrar</Link></div>
  </section></main>;
}

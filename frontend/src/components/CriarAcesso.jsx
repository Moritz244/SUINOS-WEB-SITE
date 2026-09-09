import { useState } from "react";
import { api } from "../lib/api";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
export default function CriarAcesso({ propriedades, onCreated }) {
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault(); const form = e.currentTarget; setBusy(true); setMessage("");
    try { await api.post("/usuarios", Object.fromEntries(new FormData(form))); form.reset(); setMessage("Acesso do agricultor criado com sucesso."); onCreated?.(); }
    catch (err) { setMessage(typeof err.response?.data?.detail === "string" ? err.response.data.detail : "Não foi possível criar o acesso. Verifique os campos."); }
    finally { setBusy(false); }
  }
  return <section className="bg-white border rounded-2xl p-6 mb-8"><h2 className="text-xl font-semibold">Cadastrar acesso de agricultor</h2><p className="text-sm text-slate-500 my-2">Vincule a conta à fazenda correta. O agricultor só terá acesso aos dados dessa propriedade.</p>
    <form onSubmit={submit} className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
      <div><Label htmlFor="usuario-nome">Nome</Label><Input id="usuario-nome" name="nome" required minLength={2} maxLength={120} /></div>
      <div><Label htmlFor="usuario-email">E-mail</Label><Input id="usuario-email" name="email" type="email" required /></div>
      <div><Label htmlFor="usuario-senha">Senha inicial</Label><Input id="usuario-senha" name="password" type="password" autoComplete="new-password" required minLength={10} maxLength={72} /></div>
      <div><Label htmlFor="usuario-fazenda">Fazenda</Label><select id="usuario-fazenda" name="propriedade_id" required className="border rounded-md h-10 w-full bg-white"><option value="">Selecione…</option>{propriedades.map(p => <option key={p.id} value={p.id}>{p.nome} — {p.produtor_nome}</option>)}</select></div>
      <Button type="submit" disabled={busy || !propriedades.length}>{busy ? "Criando…" : "Criar acesso"}</Button>
    </form>{message && <p role="status" className="mt-3 text-sm">{message}</p>}
  </section>;
}

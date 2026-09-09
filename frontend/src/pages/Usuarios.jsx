import { useEffect, useState } from "react";
import { api, fetchPropriedades } from "../lib/api";
import CriarAcesso from "../components/CriarAcesso";
import { Button } from "../components/ui/button";
export default function Usuarios() {
  const [users, setUsers] = useState([]), [props, setProps] = useState([]);
  const [loading, setLoading] = useState(true), [error, setError] = useState("");
  const [busy, setBusy] = useState(""), [reset, setReset] = useState(null), [search, setSearch] = useState("");
  async function load() {
    try { const [u,p] = await Promise.all([api.get("/usuarios"),fetchPropriedades()]); setUsers(u.data); setProps(p); setError(""); }
    catch { setError("Não foi possível carregar as contas."); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);
  async function action(u, type) {
    setBusy(u.id); setError(""); setReset(null);
    try {
      if (type === "status") { await api.patch(`/usuarios/${u.id}/status`, { ativo: !u.ativo }); await load(); }
      else { const {data} = await api.post(`/usuarios/${u.id}/recuperacao`); setReset({ nome: u.nome, url: `${window.location.origin}/recuperar#token=${data.token}` }); }
    } catch (e) { setError(typeof e.response?.data?.detail === "string" ? e.response.data.detail : "Não foi possível atualizar a conta."); }
    finally { setBusy(""); }
  }
  return <main className="max-w-7xl mx-auto px-4 py-10">
    <h1 className="text-3xl font-bold mb-2">Gestão de contas</h1><p className="text-slate-500 mb-6">Gerencie o acesso dos agricultores. Desativar encerra as sessões sem apagar os dados da fazenda.</p>
    <CriarAcesso propriedades={props} onCreated={load} />
    {reset && <section className="p-5 mb-5 bg-emerald-50 border rounded-xl" role="status"><h2 className="font-semibold">Recuperação de {reset.nome}</h2><p className="text-sm my-2">Link de uso único, válido por 30 minutos. Entregue ao agricultor após confirmar sua identidade. Um novo link invalida o anterior.</p><input aria-label="Link de recuperação" value={reset.url} readOnly className="w-full border rounded p-2" onFocus={e => e.target.select()} /><Button className="mt-3" onClick={() => setReset(null)}>Fechar</Button></section>}
    {error && <p role="alert" className="text-red-700 mb-4">{error} <button onClick={load} className="underline">Tentar novamente</button></p>}
    <label className="block mb-4">Buscar por nome ou e-mail<input className="block border rounded-md p-2 w-full sm:w-96 mt-1" value={search} onChange={e => setSearch(e.target.value)} /></label>
    {loading ? <p>Carregando contas…</p> : <div className="space-y-3">{users.filter(u => `${u.nome} ${u.email}`.toLowerCase().includes(search.toLowerCase())).map(u => <article key={u.id} className="bg-white border rounded-xl p-5 flex flex-wrap gap-4 justify-between items-center">
      <div className="min-w-0"><h2 className="font-semibold">{u.nome} <span className={u.ativo ? "text-emerald-700" : "text-red-700"}>· {u.ativo ? "Ativa" : "Desativada"}</span></h2><p className="break-all text-sm">{u.email}</p><p className="text-slate-500 text-sm">{u.role === "produtor" ? props.find(p => p.id === u.propriedade_id)?.nome || "Sem fazenda vinculada" : u.role}</p></div>
      {u.role === "produtor" && <div className="flex flex-wrap gap-2"><Button variant="outline" disabled={!!busy} onClick={() => action(u,"status")}>{u.ativo ? "Desativar" : "Reativar"}</Button><Button disabled={!!busy || !u.ativo} onClick={() => action(u,"reset")}>Gerar recuperação</Button></div>}
    </article>)}{!users.some(u => `${u.nome} ${u.email}`.toLowerCase().includes(search.toLowerCase())) && <p>Nenhuma conta encontrada.</p>}</div>}
  </main>;
}

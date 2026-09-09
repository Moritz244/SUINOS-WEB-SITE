import { toast } from "sonner";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
const money = cents => (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
export default function Despesas({ propId }) {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pendingDelete, setPendingDelete] = useState(null);
  async function remove() {
    setBusy(true); setError("");
    try {
      await api.delete(`/despesas/${pendingDelete.id}`);
      setRows(old => old.filter(r => r.id !== pendingDelete.id)); setPendingDelete(null); toast.success("Despesa excluída. Total atualizado.");
    } catch { setError("Não foi possível excluir a despesa. Tente novamente."); }
    finally { setBusy(false); }
  }
  useEffect(() => {
    let active = true;
    setLoading(true); setError(""); setRows([]);
    api.get("/despesas", { params: { propriedade_id: propId } }).then(r => { if (active) setRows(r.data); })
      .catch(() => { if (active) setError("Não foi possível carregar as despesas."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [propId]);
  async function submit(e) {
    e.preventDefault(); const form = e.currentTarget; const data = new FormData(form);
    setBusy(true); setError("");
    try {
      const r = await api.post("/despesas", { propriedade_id: propId, descricao: data.get("descricao"), valor: data.get("valor"), data: data.get("data") });
      setRows(old => [r.data, ...old].sort((a, b) => b.data.localeCompare(a.data))); form.reset(); toast.success("Despesa registrada. Total atualizado.");
    } catch { setError("Não foi possível registrar a despesa. Verifique os campos e tente novamente."); }
    finally { setBusy(false); }
  }
  return <section id="despesas" className="scroll-mt-24 bg-white border rounded-2xl p-6 mb-8">
    <h2 className="text-xl font-semibold">Despesas da fazenda</h2><p className="text-slate-500 text-sm mt-1">Valores registrados em todo o histórico; não incluem estimativas de bônus ou retorno.</p>
    {loading ? <p role="status">Carregando despesas…</p> : !error && <p className="text-3xl font-bold my-5">{money(rows.reduce((total, r) => total + r.valor_centavos, 0))}</p>}
    {error && <p role="alert" className="text-red-700 my-3">{error}</p>}
    {pendingDelete && <div role="alert" className="bg-red-50 border border-red-200 rounded-lg p-4 my-4">
      <p>Excluir a despesa “{pendingDelete.descricao}” de {money(pendingDelete.valor_centavos)}? Esta ação não pode ser desfeita.</p>
      <div className="flex gap-3 mt-3"><Button type="button" variant="destructive" disabled={busy} onClick={remove}>Confirmar exclusão</Button><Button type="button" variant="outline" disabled={busy} onClick={() => setPendingDelete(null)}>Cancelar</Button></div>
    </div>}
    <form onSubmit={submit} className="grid sm:grid-cols-4 gap-3 items-end my-5">
      <div><Label htmlFor="despesa-descricao">Descrição</Label><Input id="despesa-descricao" name="descricao" required minLength={2} maxLength={200} placeholder="Ex.: energia elétrica" /></div>
      <div><Label htmlFor="despesa-valor">Valor (R$)</Label><Input id="despesa-valor" name="valor" type="number" min="0.01" max="9999999999.99" step="0.01" required /></div>
      <div><Label htmlFor="despesa-data">Data</Label><Input id="despesa-data" name="data" type="date" required /></div>
      <Button disabled={busy || loading} type="submit">{busy ? "Salvando…" : "Registrar despesa"}</Button>
    </form>
    {!loading && !error && !rows.length && <p className="text-slate-500">Nenhuma despesa registrada.</p>}
    {!!rows.length && <div className="overflow-x-auto"><table className="w-full text-sm text-left"><thead><tr><th className="p-2">Data</th><th>Descrição</th><th className="text-right">Valor</th><th className="text-right">Ações</th></tr></thead><tbody>{rows.map(r => <tr key={r.id} className="border-t"><td className="p-2 whitespace-nowrap">{r.data.split("-").reverse().join("/")}</td><td className="break-words">{r.descricao}</td><td className="text-right whitespace-nowrap">{money(r.valor_centavos)}</td><td className="text-right"><Button type="button" size="sm" variant="ghost" disabled={busy} aria-label={`Excluir despesa ${r.descricao}`} onClick={() => setPendingDelete(r)}>Excluir</Button></td></tr>)}</tbody></table></div>}
  </section>;
}

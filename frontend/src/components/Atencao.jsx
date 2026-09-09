import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
const labels = { consumo_alto: "Consumo elevado", leitura_atrasada: "Leitura pendente", despesa_alta: "Despesa fora do padrão" };
export default function Atencao() {
  const [data, setData] = useState(null), [error, setError] = useState(""), [filter, setFilter] = useState("");
  async function load() { setError(""); try { setData((await api.get("/dashboard/atencao")).data); } catch { setError("Não foi possível carregar os alertas."); } }
  useEffect(() => { load(); }, []);
  return <section className="bg-white border rounded-2xl p-6 mb-8">
    <div className="flex flex-wrap justify-between gap-3"><h2 className="text-xl font-semibold">Fazendas que precisam de atenção</h2><button onClick={load} className="text-emerald-700">Atualizar alertas</button></div>
    <p className="text-sm text-slate-500 mt-2">Leituras há mais de 35 dias; consumo 15% acima das até 3 leituras anteriores; despesas do mês 50% acima da média recente, com pelo menos 2 meses de referência.</p>
    <label className="block my-4 text-sm">Filtrar alertas <select className="border rounded p-2 ml-2" value={filter} onChange={e => setFilter(e.target.value)}><option value="">Todos</option>{Object.entries(labels).map(([v,l]) => <option key={v} value={v}>{l}</option>)}</select></label>
    {error ? <p role="alert" className="text-red-700">{error}</p> : !data ? <p>Carregando alertas…</p> : <>
      <p className="text-sm mb-3">{data.alertas.length} alertas · referência: {data.data_referencia.split("-").reverse().join("/")}</p>
      <div className="grid md:grid-cols-2 gap-3">{data.alertas.filter(a => !filter || a.tipo === filter).map(a => <Link key={a.id} to={`/prefeitura/propriedades/${a.propriedade_id}`} className="border border-amber-200 rounded-xl p-4 hover:bg-amber-50">
        <p className="text-amber-700 text-xs font-semibold uppercase">{labels[a.tipo]}</p><h3 className="font-semibold mt-1">{a.propriedade_nome}</h3><p className="text-sm text-slate-600 mt-2">{a.mensagem}</p><p className="text-sm text-emerald-700 mt-2">Abrir fazenda →</p>
      </Link>)}</div>{!data.alertas.some(a => !filter || a.tipo === filter) && <p className="text-slate-500">Nenhum alerta para este filtro. Dados insuficientes não geram alertas de consumo ou despesas.</p>}
    </>}
  </section>;
}

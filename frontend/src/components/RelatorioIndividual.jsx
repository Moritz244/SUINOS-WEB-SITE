import { useState } from "react";
import { api } from "../lib/api";
import { Button } from "./ui/button";
export default function RelatorioIndividual({ propId }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  async function submit(e) {
    e.preventDefault(); const values = Object.fromEntries(new FormData(e.currentTarget));
    if (values.inicio && values.fim && values.inicio > values.fim) { setError("A data inicial deve ser anterior ou igual à final."); return; }
    setBusy(true); setError("");
    try {
      const params = Object.fromEntries(Object.entries(values).filter(([,v]) => v));
      const r = await api.get(`/propriedades/${propId}/relatorio`, { params, responseType:"blob" });
      const url = URL.createObjectURL(r.data), a = document.createElement("a"); a.href=url; a.download="relatorio-fazenda.pdf"; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch { setError("Não foi possível gerar o relatório. Tente novamente."); }
    finally { setBusy(false); }
  }
  return <section id="relatorio" className="scroll-mt-24 bg-white border rounded-2xl p-6 mb-8"><h2 className="text-xl font-semibold">Relatório individual</h2><p className="text-sm text-slate-500 mt-1">Consumo, despesas, metas e evolução mensal em PDF. Deixe as datas vazias para incluir todo o histórico.</p>
    <form onSubmit={submit} className="flex flex-wrap gap-4 items-end mt-4"><label className="text-sm">Data inicial<input type="date" name="inicio" className="block border rounded p-2 mt-1" /></label><label className="text-sm">Data final<input type="date" name="fim" className="block border rounded p-2 mt-1" /></label><Button disabled={busy}>{busy ? "Gerando…" : "Baixar relatório individual"}</Button></form>
    {error && <p role="alert" className="text-red-700 mt-3">{error}</p>}
  </section>;
}

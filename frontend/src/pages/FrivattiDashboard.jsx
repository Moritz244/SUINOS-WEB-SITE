import { useEffect, useState } from "react";
import { fetchDashFrivatti, relatorioPdfUrl } from "../lib/api";
import { KpiCard } from "../components/KpiCard";
import { Building2, TrendingUp, Award, ShieldCheck, Download, Flame, Trophy } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LabelList } from "recharts";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";

const brl = (v) => `R$ ${(v || 0).toLocaleString("pt-BR", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
const num = (v, d = 1) => (v || 0).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });

export default function FrivattiDashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchDashFrivatti().then(setData);
  }, []);

  if (!data) return <div className="max-w-7xl mx-auto px-6 py-16 text-slate-500">Carregando rede…</div>;

  const rastreabilidade = Math.round(
    (data.ranking.filter((r) => r.tem_biodigestor).length / Math.max(1, data.total_propriedades)) * 100,
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-10 fade-in">
      <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div>
          <div className="text-xs font-semibold uppercase tracking-widest text-sky-600 mb-1">Frivatti · Rede de Produtores</div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold text-slate-900">Painel da rede integrada</h1>
          <div className="text-slate-500 mt-1">Ranking de eficiência, adesão e bônus por kg do suíno</div>
        </div>
        <a href={relatorioPdfUrl()} target="_blank" rel="noreferrer" data-testid="btn-baixar-pdf-viabilidade">
          <Button className="btn-primary pill">
            <Download className="w-4 h-4 mr-1.5" /> Exportar Relatório PDF
          </Button>
        </a>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
        <KpiCard label="Propriedades na rede" value={data.total_propriedades} icon={Building2} accent="aqua" testId="kpi-total-propriedades" sub="Piloto ativo" />
        <KpiCard label="Adesão ao programa" value={num(data.adesao_pct, 0) + "%"} icon={TrendingUp} accent="emerald" testId="kpi-adesao" sub="Instalou gotejamento/nebulização" />
        <KpiCard label="Rastreabilidade CONAMA" value={rastreabilidade + "%"} icon={ShieldCheck} accent="emerald" testId="kpi-rastreabilidade" sub="Com biodigestor + destino registrado" />
        <KpiCard label="Bônus total distribuído" value={brl(data.bonus_total_brl).replace("R$ ", "")} unit="R$" icon={Award} accent="amber" testId="kpi-bonus-total" sub="Estimativa 12 meses" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-2xl border border-slate-200/70 p-6" data-testid="chart-ranking-eficiencia">
          <div className="flex items-center gap-2 mb-4">
            <Trophy className="w-5 h-5 text-amber-500" />
            <h3 className="font-display text-lg font-semibold text-slate-900">Ranking de eficiência hídrica</h3>
          </div>
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={data.ranking.slice(0, 10)} layout="vertical" margin={{ left: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" stroke="#64748b" fontSize={12} unit="%" />
              <YAxis type="category" dataKey="nome" stroke="#64748b" fontSize={11} width={140} />
              <Tooltip contentStyle={{ borderRadius: 12 }} formatter={(v) => `${v}%`} />
              <Bar dataKey="economia_pct" fill="#059669" radius={[0, 6, 6, 0]}>
                <LabelList dataKey="economia_pct" position="right" formatter={(v) => `${v}%`} style={{ fill: "#0f172a", fontSize: 11, fontWeight: 600 }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/70 p-6" data-testid="chart-biogas-rede">
          <div className="flex items-center gap-2 mb-4">
            <Flame className="w-5 h-5 text-amber-500" />
            <h3 className="font-display text-lg font-semibold text-slate-900">Biogás produzido por propriedade</h3>
          </div>
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={data.ranking}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="nome" stroke="#64748b" fontSize={10} angle={-25} textAnchor="end" height={80} interval={0} />
              <YAxis stroke="#64748b" fontSize={12} unit=" m³" />
              <Tooltip contentStyle={{ borderRadius: 12 }} />
              <Bar dataKey="biogas_m3" fill="#D97706" radius={[6, 6, 0, 0]} name="Biogás m³" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/70 overflow-hidden" data-testid="tabela-produtores">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-display text-lg font-semibold text-slate-900">Produtores integrados</h3>
          <Badge variant="secondary" className="text-xs">{data.ranking.length} propriedades</Badge>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50/70 text-slate-500 uppercase text-xs tracking-wider">
              <tr>
                <th className="text-left px-6 py-3 font-semibold">#</th>
                <th className="text-left px-6 py-3 font-semibold">Propriedade</th>
                <th className="text-left px-6 py-3 font-semibold">Município</th>
                <th className="text-right px-6 py-3 font-semibold">Suínos</th>
                <th className="text-right px-6 py-3 font-semibold">Economia</th>
                <th className="text-right px-6 py-3 font-semibold">Biogás</th>
                <th className="text-right px-6 py-3 font-semibold">Bônus est.</th>
                <th className="text-center px-6 py-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.ranking.map((r, i) => (
                <tr key={r.id} className="hover:bg-slate-50/60 transition-colors" data-testid={`row-produtor-${r.id}`}>
                  <td className="px-6 py-3 font-mono text-xs text-slate-400">{String(i + 1).padStart(2, "0")}</td>
                  <td className="px-6 py-3 font-medium text-slate-900">{r.nome}</td>
                  <td className="px-6 py-3 text-slate-600">{r.municipio}</td>
                  <td className="px-6 py-3 text-right font-mono">{r.num_suinos}</td>
                  <td className="px-6 py-3 text-right font-mono font-semibold text-emerald-600">{num(r.economia_pct, 1)}%</td>
                  <td className="px-6 py-3 text-right font-mono">{num(r.biogas_m3, 0)} m³</td>
                  <td className="px-6 py-3 text-right font-mono">{brl(r.bonus_brl)}</td>
                  <td className="px-6 py-3 text-center">
                    {r.adotou_tecnologia ? (
                      <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">Aderiu</Badge>
                    ) : (
                      <Badge variant="outline" className="text-slate-500">Pendente</Badge>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

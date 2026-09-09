import { Link } from "react-router-dom";
import Atencao from "../components/Atencao";
import { useEffect, useState } from "react";
import { fetchDashPrefeitura, relatorioPdfUrl } from "../lib/api";
import { KpiCard } from "../components/KpiCard";
import { Landmark, Droplets, Flame, Download, MapPin, TrendingUp, Coins } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, RadialBarChart, RadialBar } from "recharts";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";

const brl = (v) => `R$ ${(v || 0).toLocaleString("pt-BR", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
const num = (v, d = 1) => (v || 0).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
const COLORS = ["#059669", "#0284C7", "#D97706", "#0D9488", "#65A30D"];

export default function PrefeituraDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchDashPrefeitura().then(setData).catch(() => setError("Não foi possível carregar os indicadores. Recarregue a página para tentar novamente."));
  }, []);

  if (error) return <p role="alert" className="p-10 text-red-700">{error}</p>;
  if (!data) return <div className="max-w-7xl mx-auto px-6 py-16 text-slate-500">Carregando indicadores…</div>;

  const munData = data.municipios.map((m) => ({ name: m.municipio, value: m.propriedades }));
  const adesaoData = [{ name: "Adesão", value: data.adesao_pct, fill: "#059669" }];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-10 fade-in">
      <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div>
          <div className="text-xs font-semibold uppercase tracking-widest text-amber-600 mb-1">Prefeitura · Gestão Pública</div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold text-slate-900">Visão geral das fazendas</h1>
          <div className="text-slate-500 mt-1">Indicadores agregados de {data.total_propriedades} propriedades cadastradas</div>
        </div>
        <a href={relatorioPdfUrl()} target="_blank" rel="noreferrer" data-testid="btn-baixar-pdf-viabilidade">
          <Button className="btn-primary pill">
            <Download className="w-4 h-4 mr-1.5" /> Gerar Relatório de Viabilidade (PDF)
          </Button>
        </a>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
        <KpiCard label="Economia de água estimada" value={num(data.economia_m3, 0)} unit="m³" icon={Droplets} accent="aqua" testId="kpi-agua-economizada" sub={`${num(data.economia_pct, 1)}% vs referência histórica`} />
        <KpiCard label="Biogás gerado" value={num(data.biogas_m3, 0)} unit="m³" icon={Flame} accent="amber" testId="kpi-biogas-gerado" sub="Estimativa por fator de conversão" />
        <KpiCard label="Retorno estimado" value={brl(data.retorno_economico_brl).replace("R$ ", "")} unit="R$" icon={Coins} accent="emerald" testId="kpi-retorno-economico" sub="Água + biogás (piloto)" />
        <KpiCard label="Adesão do piloto" value={num(data.adesao_pct, 0) + "%"} icon={TrendingUp} accent="emerald" testId="kpi-adesao-piloto" sub={`${data.total_propriedades} propriedades`} />
      </div>

      <Atencao />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-2xl border border-slate-200/70 p-6" data-testid="chart-municipios">
          <div className="flex items-center gap-2 mb-4">
            <MapPin className="w-5 h-5 text-sky-500" />
            <h3 className="font-display text-lg font-semibold text-slate-900">Distribuição por município</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={munData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={55} paddingAngle={2}>
                {munData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 12 }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/70 p-6" data-testid="chart-adesao">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-emerald-500" />
            <h3 className="font-display text-lg font-semibold text-slate-900">Impacto agregado</h3>
          </div>
          <div className="grid grid-cols-2 h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart innerRadius="55%" outerRadius="90%" data={adesaoData} startAngle={90} endAngle={-270}>
                <RadialBar background dataKey="value" cornerRadius={20} />
                <text x="50%" y="48%" textAnchor="middle" dominantBaseline="middle" className="font-display" style={{ fontSize: 34, fontWeight: 800, fill: "#059669" }}>{data.adesao_pct}%</text>
                <text x="50%" y="60%" textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 11, fill: "#64748b" }}>Adesão</text>
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="flex flex-col justify-center gap-4 pl-4">
              <div>
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Consumo total</div>
                <div className="font-display text-2xl font-bold text-slate-900">{num(data.total_consumo_m3, 0)} <span className="text-sm text-slate-500">m³</span></div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Economia hídrica</div>
                <div className="font-display text-2xl font-bold text-emerald-600">{num(data.economia_m3, 0)} <span className="text-sm text-slate-500">m³</span></div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-wider text-slate-500 font-semibold">Retorno estimado</div>
                <div className="font-display text-2xl font-bold text-amber-600">{brl(data.retorno_economico_brl)}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <section className="bg-white border rounded-2xl p-6 mb-8">
        <h2 className="text-xl font-semibold">Despesas registradas de todas as fazendas</h2>
        <p className="text-3xl font-bold mt-3">{(data.despesas_total_centavos / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</p>
        <p className="text-sm text-slate-500 mt-2">Total de todo o histórico. Abra uma propriedade para consultar os lançamentos.</p>
      </section>

      <div className="bg-white rounded-2xl border border-slate-200/70 overflow-hidden" data-testid="lista-propriedades-prefeitura">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Landmark className="w-5 h-5 text-amber-500" />
            <h3 className="font-display text-lg font-semibold text-slate-900">Encontre uma fazenda</h3>
          </div>
          <Badge variant="secondary" className="text-xs">{data.total_propriedades} unidades</Badge>
        </div>
        <div className="px-6 pt-5"><label className="block text-sm font-medium">Buscar fazenda, produtor ou município<input className="block w-full border rounded-lg p-3 mt-2" value={search} onChange={e => setSearch(e.target.value)} placeholder="Digite para encontrar uma propriedade" /></label><p className="text-sm text-slate-500 mt-2">Abra a fazenda para consultar leituras, despesas e relatórios. Para gerenciar acessos, use <Link className="text-emerald-700 underline" to="/prefeitura/contas">Contas</Link>.</p></div>
        {!data.propriedades.length && <p className="p-6 text-slate-500">Nenhuma fazenda cadastrada. O agricultor pode criar sua conta e propriedade em Criar conta.</p>}
        {!!data.propriedades.length && !data.propriedades.some(p => `${p.nome} ${p.produtor_nome} ${p.municipio}`.toLocaleLowerCase("pt-BR").includes(search.toLocaleLowerCase("pt-BR"))) && <p className="p-6 text-slate-500">Nenhuma fazenda encontrada. Tente outro nome ou município.</p>}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
          {data.propriedades.filter(p => `${p.nome} ${p.produtor_nome} ${p.municipio}`.toLocaleLowerCase("pt-BR").includes(search.toLocaleLowerCase("pt-BR"))).map((p) => (
            <Link to={`/prefeitura/propriedades/${p.id}`} key={p.id} className="border border-slate-200 rounded-xl p-4 hover:border-emerald-400 hover:shadow-md transition-all" data-testid={`prop-card-${p.id}`}>
              <div className="flex items-start justify-between mb-2">
                <div className="font-semibold text-slate-900">{p.nome}</div>
                {p.tem_biodigestor && <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 text-[10px]">Biodigestor</Badge>}
              </div>
              <div className="text-xs text-slate-500 flex items-center gap-1"><MapPin className="w-3 h-3" />{p.municipio}</div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <div className="text-slate-400 uppercase tracking-wider text-[10px]">Suínos</div>
                  <div className="font-mono font-semibold text-slate-900">{p.num_suinos}</div>
                </div>
                <div>
                  <div className="text-slate-400 uppercase tracking-wider text-[10px]">Área</div>
                  <div className="font-mono font-semibold text-slate-900">{p.area_m2} m²</div>
                </div>
              </div>
              <p className="text-sm mt-3">Despesas: {(p.despesas_centavos / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</p>
              <p className="text-sm font-semibold text-emerald-700 mt-3">Ver consumo, despesas e detalhes →</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

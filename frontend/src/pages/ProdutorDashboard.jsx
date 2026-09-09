import { Link, useParams } from "react-router-dom";
import { useAuth } from "../lib/auth";
import Despesas from "../components/Despesas";
import RelatorioIndividual from "../components/RelatorioIndividual";
import { useEffect, useState } from "react";
import { fetchPropriedade, createLeitura, createDejeto, resolverAlerta } from "../lib/api";
import { KpiCard } from "../components/KpiCard";
import { Droplets, Gauge, Award, AlertTriangle, Flame, Camera, CheckCircle2, TrendingDown } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar, Legend } from "recharts";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "../components/ui/dialog";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";

const brl = (v) => `R$ ${(v || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const num = (v, digits = 1) => (v || 0).toLocaleString("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits });

export default function ProdutorDashboard() {
  const { user } = useAuth();
  const { propId } = useParams();
  const selected = user.role === "produtor" ? user.propriedade_id : propId;
  const [error, setError] = useState("");
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [openLeitura, setOpenLeitura] = useState(false);
  const [openDejeto, setOpenDejeto] = useState(false);

  const loadDetail = async (id) => {
    try { setDetail(await fetchPropriedade(id)); }
    catch { toast.error("Não foi possível atualizar a propriedade."); }
  };
  useEffect(() => {
    let active = true;
    setLoading(true); setDetail(null); setError("");
    if (!selected) { setLoading(false); return; }
    fetchPropriedade(selected).then(d => { if (active) setDetail(d); })
      .catch(() => { if (active) setError("Não foi possível carregar esta fazenda. Verifique seu acesso e tente novamente."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [selected]);
  if (error) return <p role="alert" className="p-10 text-red-700">{error}</p>;
  if (!selected) return <p className="p-10">Sua conta ainda não tem uma fazenda vinculada. Entre em contato com a prefeitura.</p>;

  if (loading || !detail) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-16">
        <div className="animate-pulse space-y-4">
          <div className="h-10 bg-slate-100 rounded-lg w-1/3" />
          <div className="grid grid-cols-4 gap-4">
            {[1,2,3,4].map(i => <div key={i} className="h-40 bg-slate-100 rounded-2xl" />)}
          </div>
        </div>
      </div>
    );
  }

  const prop = detail.propriedade;
  const resumo = detail.resumo;
  const chartData = detail.leituras.map((l, i) => ({
    mes: new Date(l.data_leitura).toLocaleDateString("pt-BR", { month: "short" }),
    consumo: l.consumo_m3,
    meta: resumo.meta_m3,
    idx: i,
  }));
  const biogasData = detail.dejetos.map((d) => ({
    mes: new Date(d.data_registro).toLocaleDateString("pt-BR", { month: "short" }),
    biogas: d.biogas_m3,
    dejeto: d.volume_kg / 1000,
  }));

  const alertasAtivos = detail.alertas.filter(a => !a.resolvido);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-10 fade-in">
      <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div>
          <div className="text-xs font-semibold uppercase tracking-widest text-emerald-600 mb-1">{user.role === "prefeitura" ? "Detalhes da propriedade" : "Painel do Produtor"}</div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold text-slate-900">{prop.nome}</h1>
          <div className="text-slate-500 mt-1">{prop.municipio} · {prop.num_suinos} suínos · Hidrômetro {prop.hidrometro_serial}</div>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <Dialog open={openLeitura} onOpenChange={setOpenLeitura}>
            <DialogTrigger asChild>
              <Button className="btn-primary pill" data-testid="btn-open-nova-leitura">
                <Gauge className="w-4 h-4 mr-1.5" /> Nova leitura
              </Button>
            </DialogTrigger>
            <NovaLeituraDialog propId={prop.id} onSaved={() => { setOpenLeitura(false); loadDetail(prop.id); }} />
          </Dialog>

          <Dialog open={openDejeto} onOpenChange={setOpenDejeto}>
            <DialogTrigger asChild>
              <Button variant="outline" className="pill border-slate-300" data-testid="btn-open-nova-dejeto">
                <Flame className="w-4 h-4 mr-1.5" /> Registrar dejetos
              </Button>
            </DialogTrigger>
            <NovoDejetoDialog propId={prop.id} onSaved={() => { setOpenDejeto(false); loadDetail(prop.id); }} />
          </Dialog>
        </div>
      </div>

      {user.role === "prefeitura" && <Link to="/prefeitura" className="inline-block mb-5 text-emerald-700">← Voltar para todas as fazendas</Link>}
      <section className="bg-emerald-50 border border-emerald-100 rounded-2xl p-5 mb-6">
        <h2 className="font-semibold text-lg">{detail.leituras.length ? "Seu próximo passo" : "Comece pela primeira leitura"}</h2>
        <p className="text-sm text-slate-600 mt-2">{detail.leituras.length ? "Registre a próxima leitura para acompanhar o consumo desde o último registro. Use as despesas e o relatório para revisar a evolução da fazenda." : "Informe o número acumulado do hidrômetro. A primeira leitura vira a referência; o consumo aparece a partir da segunda."}</p>
        <nav aria-label="Ações da fazenda" className="flex flex-wrap gap-4 mt-4 text-sm font-semibold text-emerald-800">
          <button onClick={() => setOpenLeitura(true)}>1. Registrar água</button><a href="#despesas">2. Registrar despesas</a><a href="#relatorio">3. Consultar relatório</a>
        </nav>
      </section>
      {/* KPIS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-8">
        <KpiCard label="Consumo entre leituras" value={num(resumo.ultimo_consumo_m3, 1)} unit="m³" icon={Droplets} accent="aqua" testId="kpi-consumo-ultimo" sub={`Referência histórica: ${num(resumo.baseline_m3, 1)} m³`} />
        <KpiCard label="Meta de consumo" value={num(resumo.meta_m3, 1)} unit="m³" icon={Gauge} accent="emerald" testId="kpi-meta" sub={`Redução alvo: ${prop.meta_reducao_pct}%`} />
        <KpiCard label="Bônus estimado" value={brl(resumo.bonus_estimado_brl).replace("R$ ", "")} unit="R$" icon={Award} accent="amber" testId="kpi-bonus" sub="Simulação; não é pagamento garantido" />
        <KpiCard label="Alertas ativos" value={resumo.alertas_ativos} icon={AlertTriangle} accent="amber" testId="kpi-alertas" sub={resumo.alertas_ativos === 0 ? "Sem alertas registrados" : "Verificar"} />
      </div>

      <Despesas key={prop.id} propId={prop.id} />
      <RelatorioIndividual key={`report-${prop.id}`} propId={prop.id} />
      {/* CHARTS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-2xl border border-slate-200/70 p-6" data-testid="chart-consumo">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-display text-lg font-semibold text-slate-900">Consumo x Meta</h3>
              <div className="text-xs text-slate-500">m³ por mês</div>
            </div>
            <TrendingDown className="w-5 h-5 text-emerald-500" />
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="mes" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Legend />
              <Line type="monotone" dataKey="consumo" stroke="#0284C7" strokeWidth={3} dot={{ r: 4 }} name="Consumo" />
              <Line type="monotone" dataKey="meta" stroke="#059669" strokeWidth={2} strokeDasharray="6 4" dot={false} name="Meta" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/70 p-6" data-testid="chart-biogas">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-display text-lg font-semibold text-slate-900">Biogás x Dejetos tratados</h3>
              <div className="text-xs text-slate-500">m³ biogás · t dejeto</div>
            </div>
            <Flame className="w-5 h-5 text-amber-500" />
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={biogasData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="mes" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
              <Legend />
              <Bar dataKey="biogas" fill="#D97706" name="Biogás (m³)" radius={[6, 6, 0, 0]} />
              <Bar dataKey="dejeto" fill="#059669" name="Dejeto (t)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ALERTAS */}
      <div className="bg-white rounded-2xl border border-slate-200/70 p-6" data-testid="lista-alertas">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-lg font-semibold text-slate-900">Alertas</h3>
          <Badge variant="outline" className="text-xs">{alertasAtivos.length} ativos</Badge>
        </div>
        {detail.alertas.length === 0 ? (
          <div className="text-slate-500 text-sm py-6 text-center">Nenhum alerta registrado.</div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {detail.alertas.slice(0, 8).map((a) => (
              <li key={a.id} className="py-3 flex items-center justify-between gap-4" data-testid={`alerta-${a.id}`}>
                <div className="flex items-center gap-3">
                  {a.tipo === "meta_atingida" ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0" />
                  )}
                  <div>
                    <div className="text-sm font-medium text-slate-900">{a.mensagem}</div>
                    <div className="text-xs text-slate-500">{new Date(a.created_at).toLocaleDateString("pt-BR")}</div>
                  </div>
                </div>
                {!a.resolvido && (
                  <Button size="sm" variant="ghost" onClick={async () => { await resolverAlerta(a.id); toast.success("Alerta resolvido"); loadDetail(prop.id); }} data-testid={`btn-resolver-${a.id}`}>
                    Resolver
                  </Button>
                )}
                {a.resolvido && <Badge variant="secondary" className="text-xs">Resolvido</Badge>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function NovaLeituraDialog({ propId, onSaved }) {
  const [leitura, setLeitura] = useState("");
  const [data, setData] = useState(new Date().toISOString().slice(0, 10));
  const [obs, setObs] = useState("");
  const [foto, setFoto] = useState(null);
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    if (!leitura) { toast.error("Informe a leitura"); return; }
    setSaving(true);
    try {
      const fd = new FormData();
      fd.append("propriedade_id", propId);
      fd.append("leitura_m3", leitura);
      fd.append("data_leitura", new Date(data).toISOString());
      if (obs) fd.append("observacao", obs);
      if (foto) fd.append("foto", foto);
      const result = await createLeitura(fd);
      if (result.aviso) toast.warning(result.aviso);
      toast.success("Leitura registrada");
      onSaved();
    } catch (e) {
      toast.error(typeof e.response?.data?.detail === "string" ? e.response.data.detail : "Não foi possível salvar a leitura. Tente novamente.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <DialogContent data-testid="dialog-nova-leitura">
      <DialogHeader>
        <DialogTitle>Nova leitura do hidrômetro</DialogTitle>
      </DialogHeader>
      <div className="space-y-4 py-2">
        <div>
          <Label htmlFor="leitura">Leitura (m³)</Label>
          <Input id="leitura" type="number" step="0.01" value={leitura} onChange={(e) => setLeitura(e.target.value)} data-testid="input-leitura-m3" />
        </div>
        <div>
          <Label htmlFor="data">Data da leitura</Label>
          <Input id="data" type="date" value={data} onChange={(e) => setData(e.target.value)} data-testid="input-data-leitura" />
        </div>
        <div>
          <Label htmlFor="foto">Foto do hidrômetro (opcional)</Label>
          <div className="flex items-center gap-2 mt-1">
            <Camera className="w-4 h-4 text-slate-400" />
            <Input id="foto" type="file" accept="image/*" onChange={(e) => setFoto(e.target.files?.[0])} data-testid="input-foto-hidrometro" />
          </div>
        </div>
        <div>
          <Label htmlFor="obs">Observação</Label>
          <Textarea id="obs" value={obs} onChange={(e) => setObs(e.target.value)} data-testid="input-observacao" />
        </div>
      </div>
      <DialogFooter>
        <Button onClick={submit} disabled={saving} className="btn-primary pill" data-testid="btn-salvar-leitura">
          {saving ? "Salvando..." : "Salvar leitura"}
        </Button>
      </DialogFooter>
    </DialogContent>
  );
}

function NovoDejetoDialog({ propId, onSaved }) {
  const [volume, setVolume] = useState("");
  const [destino, setDestino] = useState("fertirrigação");
  const [aguaDestino, setAguaDestino] = useState("reúso na granja");
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    if (!volume) { toast.error("Informe o volume"); return; }
    setSaving(true);
    try {
      await createDejeto({
        propriedade_id: propId,
        volume_kg: parseFloat(volume),
        destino_digestato: destino,
        destino_agua_tratada: aguaDestino,
        conforme_conama: true,
      });
      toast.success("Registro de dejetos salvo");
      onSaved();
    } catch (e) {
      toast.error("Erro ao salvar");
    } finally {
      setSaving(false);
    }
  };

  const biogasEst = volume ? (parseFloat(volume) * 0.062).toFixed(1) : "0";

  return (
    <DialogContent data-testid="dialog-novo-dejeto">
      <DialogHeader>
        <DialogTitle>Registrar dejetos tratados</DialogTitle>
      </DialogHeader>
      <div className="space-y-4 py-2">
        <div>
          <Label htmlFor="volume">Volume tratado (kg)</Label>
          <Input id="volume" type="number" step="0.1" value={volume} onChange={(e) => setVolume(e.target.value)} data-testid="input-volume-dejeto" />
          <div className="mt-1 text-xs text-slate-500">Estimativa de biogás: <span className="font-mono font-bold text-amber-600">{biogasEst} m³</span> (fator Embrapa 0,062)</div>
        </div>
        <div>
          <Label htmlFor="destino">Destino do digestato</Label>
          <Select value={destino} onValueChange={setDestino}>
            <SelectTrigger id="destino" data-testid="select-destino-digestato"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="fertirrigação">Fertirrigação</SelectItem>
              <SelectItem value="lavoura milho">Lavoura milho</SelectItem>
              <SelectItem value="pastagem">Pastagem</SelectItem>
              <SelectItem value="compostagem">Compostagem</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label htmlFor="agua">Destino da água tratada</Label>
          <Input id="agua" value={aguaDestino} onChange={(e) => setAguaDestino(e.target.value)} data-testid="input-destino-agua" />
        </div>
      </div>
      <DialogFooter>
        <Button onClick={submit} disabled={saving} className="btn-primary pill" data-testid="btn-salvar-dejeto">
          {saving ? "Salvando..." : "Salvar registro"}
        </Button>
      </DialogFooter>
    </DialogContent>
  );
}

import { Link } from "react-router-dom";
import { Droplets, Gauge, Recycle, Flame, ArrowRight, Tractor, Building2, Landmark, CheckCircle2 } from "lucide-react";

const STEPS = [
  { icon: Gauge, title: "Medir", desc: "Leitura mensal do hidrômetro por propriedade, com foto pra auditoria.", color: "from-emerald-500 to-emerald-600" },
  { icon: Droplets, title: "Reduzir", desc: "Meta de -10% sobre a baseline, alertas de vazamento e ranking de eficiência.", color: "from-sky-500 to-sky-600" },
  { icon: Recycle, title: "Tratar", desc: "Registro de dejetos + destino do digestato conforme CONAMA.", color: "from-teal-500 to-teal-600" },
  { icon: Flame, title: "Reaproveitar", desc: "Estimativa de biogás (m³) via fator Embrapa e aproveitamento energético.", color: "from-amber-500 to-amber-600" },
];

const PROFILES = [
  { role: "produtor", icon: Tractor, title: "Produtor Rural", desc: "Acompanhe consumo, bata metas e ganhe bônus Frivatti.", path: "/produtor", accent: "emerald" },
  { role: "frivatti", icon: Building2, title: "Frivatti", desc: "Rede de produtores, ranking de eficiência e rastreabilidade.", path: "/frivatti", accent: "sky" },
  { role: "prefeitura", icon: Landmark, title: "Prefeitura", desc: "KPIs agregados do piloto e relatório PDF de viabilidade.", path: "/prefeitura", accent: "amber" },
];

export default function Landing() {
  return (
    <div className="fade-in">
      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <div className="absolute -top-32 -left-32 w-[520px] h-[520px] rounded-full bg-emerald-100/70 blur-3xl" />
          <div className="absolute top-20 -right-20 w-[420px] h-[420px] rounded-full bg-sky-100/70 blur-3xl" />
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 pt-16 pb-20 lg:pt-24 lg:pb-28 grid lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-7">
            <div className="inline-flex items-center gap-2 rounded-full bg-white border border-emerald-200 px-3 py-1.5 shadow-sm mb-6">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-semibold uppercase tracking-widest text-emerald-700">Piloto · 10 Propriedades · 10 Meses</span>
            </div>
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.05]" data-testid="hero-title">
              Gestão hídrica e de dejetos<br />
              <span className="bg-gradient-to-r from-emerald-600 to-sky-600 bg-clip-text text-transparent">para a suinocultura</span>
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl leading-relaxed">
              O AquaSuíno mede o consumo de água, monitora dejetos, estima biogás e prova viabilidade
              econômica pra uma rede produtor + frigorífico + prefeitura.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/prefeitura" className="btn-primary pill px-6 py-3 font-semibold inline-flex items-center gap-2" data-testid="cta-explorar-demo">
                Explorar Piloto Demo <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/produtor" className="pill px-6 py-3 font-semibold inline-flex items-center gap-2 bg-white border border-slate-200 hover:border-slate-300 text-slate-800 transition-colors" data-testid="cta-produtor">
                Sou produtor <Tractor className="w-4 h-4" />
              </Link>
            </div>
            <div className="mt-10 grid grid-cols-3 gap-4 max-w-xl">
              {[
                { v: "10", l: "Propriedades" },
                { v: "10", l: "Meses de dados" },
                { v: "-10%", l: "Meta hídrica" },
              ].map((s, i) => (
                <div key={i} className="border-l-2 border-emerald-500 pl-3">
                  <div className="font-display text-3xl font-black text-slate-900">{s.v}</div>
                  <div className="text-xs uppercase tracking-wider text-slate-500 mt-0.5">{s.l}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="lg:col-span-5 relative">
            <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-white/40">
              <img
                src="https://images.unsplash.com/photo-1757342396554-c904a02afc8d?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200"
                alt="Granja sustentável"
                className="w-full h-[420px] object-cover"
              />
              <div className="absolute bottom-4 left-4 right-4 glass rounded-2xl p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500 text-white flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-900">Conforme CONAMA</div>
                  <div className="text-xs text-slate-600">Rastreabilidade digestato + reúso hídrico</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* MODELO 4 PASSOS */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-16 lg:py-24">
        <div className="mb-12 max-w-2xl">
          <div className="text-xs font-semibold uppercase tracking-widest text-emerald-600 mb-3">O modelo</div>
          <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-slate-900">
            Medir → Reduzir → Tratar → Reaproveitar
          </h2>
          <p className="mt-3 text-slate-600 text-lg">
            Quatro passos para transformar granjas em unidades sustentáveis e economicamente viáveis.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {STEPS.map((s, i) => {
            const Icon = s.icon;
            return (
              <div key={s.title} className="slide-in relative bg-white rounded-2xl p-6 border border-slate-200/70 hover:border-slate-300 hover:shadow-lg transition-all" style={{ animationDelay: `${i * 80}ms` }} data-testid={`step-${s.title.toLowerCase()}`}>
                <div className="flex items-center gap-3 mb-4">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${s.color} flex items-center justify-center text-white shadow-md`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="font-mono text-xs text-slate-400">0{i + 1}</div>
                </div>
                <h3 className="font-display text-xl font-bold text-slate-900">{s.title}</h3>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">{s.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* PROFILES */}
      <section className="bg-white border-y border-slate-200/70">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-16 lg:py-24">
          <div className="mb-10 max-w-2xl">
            <div className="text-xs font-semibold uppercase tracking-widest text-sky-600 mb-3">3 perfis, 3 visões</div>
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-slate-900">Escolha um perfil para explorar</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {PROFILES.map((p) => {
              const Icon = p.icon;
              const bg = p.accent === "emerald" ? "from-emerald-500 to-teal-600" : p.accent === "sky" ? "from-sky-500 to-blue-600" : "from-amber-500 to-orange-600";
              return (
                <Link key={p.role} to={p.path} data-testid={`profile-card-${p.role}`} className="group relative rounded-2xl bg-slate-50 hover:bg-white border border-slate-200 hover:shadow-xl hover:-translate-y-1 transition-all p-6 overflow-hidden">
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${bg} flex items-center justify-center text-white mb-5 shadow-lg`}>
                    <Icon className="w-7 h-7" />
                  </div>
                  <h3 className="font-display text-2xl font-bold text-slate-900">{p.title}</h3>
                  <p className="mt-2 text-slate-600 text-sm">{p.desc}</p>
                  <div className="mt-6 inline-flex items-center gap-1.5 text-sm font-semibold text-emerald-600 group-hover:gap-2 transition-all">
                    Abrir dashboard <ArrowRight className="w-4 h-4" />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-200/70 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 flex flex-wrap items-center justify-between gap-4 text-sm text-slate-500">
          <div>© 2026 AquaSuíno · Projeto-piloto Frivatti + Prefeitura + Produtores</div>
          <div className="flex items-center gap-2">
            <Droplets className="w-4 h-4 text-emerald-500" />
            <span>Medir → Reduzir → Tratar → Reaproveitar</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

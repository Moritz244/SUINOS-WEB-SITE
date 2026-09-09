import { Link } from "react-router-dom";
import { ArrowRight, Droplets, Gauge, Wallet, Landmark, Tractor, ShieldCheck, FileText } from "lucide-react";
import { useAuth, homeFor } from "../lib/auth";

export default function Home() {
  const { user } = useAuth();
  return <main>
    <section className="max-w-7xl mx-auto px-5 sm:px-8 py-14 lg:py-20 grid lg:grid-cols-2 gap-12 items-center">
      <div><p className="text-xs font-bold tracking-widest uppercase text-emerald-700 mb-5">Água, despesas e informação no mesmo lugar</p>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 leading-tight">Cuide da sua fazenda.<br/><span className="text-emerald-600">Entenda cada gasto.</span></h1>
        <p className="text-lg text-slate-600 leading-relaxed mt-6 max-w-xl">O AquaSuíno ajuda agricultores e prefeituras a acompanhar o consumo de água, registrar despesas e identificar fazendas que precisam de atenção.</p>
        <p className="text-slate-500 leading-relaxed mt-3">Troque anotações espalhadas por um histórico organizado para decidir o que verificar e onde agir.</p>
        <div className="flex flex-wrap gap-3 mt-7"><Link to={user ? homeFor(user) : "/cadastro"} className="btn-primary rounded-full px-6 py-3 font-semibold inline-flex items-center gap-2">{user ? "Abrir meu painel" : "Cadastrar minha fazenda"}<ArrowRight className="w-4 h-4"/></Link><Link to="/demonstracao" className="rounded-full border border-slate-300 bg-white px-6 py-3 font-semibold text-slate-700">Experimentar em 2 minutos</Link></div>
        {!user && <p className="mt-4 text-sm text-slate-500">Já tem acesso? <Link to="/login" className="font-semibold text-emerald-700 underline underline-offset-4">Entrar na minha conta</Link></p>}
        <p className="mt-7 flex items-center gap-2 text-sm text-slate-500"><ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0"/>Cada agricultor acessa somente sua própria fazenda.</p>
      </div>
      <div className="rounded-3xl bg-[#073f33] p-6 sm:p-9 text-white shadow-xl">
        <p className="text-emerald-200 text-xs font-bold tracking-widest uppercase">Uma decisão começa com um registro</p><h2 className="text-2xl font-semibold mt-3 mb-6">Da leitura à próxima ação</h2>
        {[{icon:Gauge,title:"Registre a leitura",text:"Informe o número do hidrômetro e a data."},{icon:Droplets,title:"Veja quanto consumiu",text:"O sistema calcula a diferença entre as leituras."},{icon:Wallet,title:"Acompanhe suas despesas",text:"Guarde os lançamentos e consulte o total."},{icon:FileText,title:"Decida com o histórico",text:"Compare os dados e baixe o relatório da fazenda."}].map((s,i)=><div key={s.title} className="flex gap-4 py-4 border-t border-white/10"><div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center shrink-0"><s.icon className="w-5 h-5 text-emerald-200"/></div><div><p className="font-semibold">{i+1}. {s.title}</p><p className="text-sm text-emerald-100/75 mt-1 leading-relaxed">{s.text}</p></div></div>)}
      </div>
    </section>
    <section className="bg-white border-y border-slate-200"><div className="max-w-7xl mx-auto px-5 sm:px-8 py-14"><h2 className="text-3xl font-bold text-slate-900">O que você pode fazer aqui</h2><div className="grid md:grid-cols-2 gap-6 mt-7">
      <article className="rounded-2xl p-7 border bg-emerald-50/40"><Tractor className="text-emerald-600 w-8 h-8"/><h3 className="text-xl font-bold mt-4">Para o agricultor</h3><p className="text-slate-600 mt-3 leading-relaxed">Registre água, despesas e dejetos. Consulte o histórico da sua fazenda e acompanhe a meta de consumo.</p><Link to={user ? homeFor(user) : "/cadastro"} className="inline-flex items-center gap-2 font-semibold text-emerald-700 mt-5">{user ? "Acessar meu painel" : "Começar meu cadastro"}<ArrowRight className="w-4 h-4"/></Link><p className="text-sm text-slate-500 mt-3">Sua fazenda já está cadastrada? Peça à prefeitura um acesso vinculado a ela.</p></article>
      <article className="rounded-2xl p-7 border bg-slate-50"><Landmark className="text-sky-600 w-8 h-8"/><h3 className="text-xl font-bold mt-4">Para a prefeitura</h3><p className="text-slate-600 mt-3 leading-relaxed">Encontre uma fazenda, confira alertas, consulte despesas e relatórios e gerencie o acesso dos agricultores.</p><Link to={user ? homeFor(user) : "/login"} className="inline-flex items-center gap-2 font-semibold text-sky-700 mt-5">{user ? "Continuar no meu painel" : "Entrar com acesso institucional"}<ArrowRight className="w-4 h-4"/></Link><p className="text-sm text-slate-500 mt-3">O perfil institucional é concedido pela administração do sistema.</p></article>
    </div></div></section>
    <section className="max-w-7xl mx-auto px-5 sm:px-8 py-14 grid md:grid-cols-2 gap-8"><div><h2 className="text-2xl font-bold">Experimente o caminho completo</h2><p className="text-slate-600 mt-3 leading-relaxed">Na demonstração, você registra uma leitura, adiciona uma despesa e vê o resultado. Os dados são fictícios e ficam apenas nessa experiência.</p><Link to="/demonstracao" className="inline-flex items-center gap-2 text-emerald-700 font-semibold mt-4">Iniciar demonstração guiada<ArrowRight className="w-4 h-4"/></Link></div><div className="border-l-4 border-emerald-500 pl-6"><h2 className="font-semibold text-lg">Informação para apoiar decisões</h2><p className="text-slate-600 mt-3 leading-relaxed">Metas, biogás e retorno econômico são estimativas. Os registros ajudam no acompanhamento; resultados de economia, viabilidade e conformidade precisam ser verificados na operação da fazenda.</p></div></section>
    <footer className="border-t p-6 text-center text-sm text-slate-500">AquaSuíno · Gestão de água e despesas na suinocultura</footer>
  </main>;
}

import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth, homeFor } from "../lib/auth";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";

export default function Cadastro() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  if (loading) return <p className="p-10">Verificando acesso…</p>;
  if (user) return <Navigate to={homeFor(user)} replace />;
  async function submit(e) {
    e.preventDefault(); setError("");
    const data = Object.fromEntries(new FormData(e.currentTarget));
    if (data.password !== data.confirmacao) { setError("As senhas não coincidem."); return; }
    delete data.confirmacao;
    data.num_suinos = Number(data.num_suinos); data.area_m2 = Number(data.area_m2);
    setBusy(true);
    try {
      await api.post("/auth/cadastro", data);
      navigate("/login", { replace: true, state: { cadastro: true, email: data.email } });
    } catch (err) {
      setError(typeof err.response?.data?.detail === "string" ? err.response.data.detail : "Não foi possível criar a conta. Confira os campos e tente novamente.");
    } finally { setBusy(false); }
  }
  return <main className="max-w-2xl mx-auto px-4 py-10"><form onSubmit={submit} className="bg-white border rounded-2xl p-6 sm:p-8 space-y-6">
    <div><h1 className="text-3xl font-bold">Criar conta</h1><p className="text-slate-500 mt-2">Cadastre seu acesso de agricultor e sua fazenda.</p><p className="text-sm text-slate-500 mt-2">Se sua fazenda já está cadastrada, solicite à prefeitura um acesso vinculado a ela para evitar duplicidade.</p></div>
    <fieldset><legend className="text-lg font-semibold mb-3">Seus dados</legend><div className="grid sm:grid-cols-2 gap-4">
      <div><Label htmlFor="cad-nome">Nome completo</Label><Input id="cad-nome" name="nome" autoComplete="name" required minLength={2} maxLength={120} /></div>
      <div><Label htmlFor="cad-email">E-mail</Label><Input id="cad-email" name="email" type="email" autoComplete="email" required /></div>
      <div><Label htmlFor="cad-password">Senha</Label><Input id="cad-password" name="password" type="password" autoComplete="new-password" required minLength={10} maxLength={72} /><p className="text-xs text-slate-500 mt-1">Pelo menos 10 caracteres.</p></div>
      <div><Label htmlFor="cad-confirmacao">Confirmar senha</Label><Input id="cad-confirmacao" name="confirmacao" type="password" autoComplete="new-password" required minLength={10} maxLength={72} /></div>
    </div></fieldset>
    <fieldset><legend className="text-lg font-semibold mb-3">Sua fazenda</legend><div className="grid sm:grid-cols-2 gap-4">
      <div><Label htmlFor="cad-fazenda">Nome da fazenda</Label><Input id="cad-fazenda" name="fazenda" required minLength={2} maxLength={120} /></div>
      <div><Label htmlFor="cad-municipio">Município / UF</Label><Input id="cad-municipio" name="municipio" placeholder="Ex.: Itapiranga / SC" required minLength={2} maxLength={120} /></div>
      <div><Label htmlFor="cad-suinos">Quantidade de suínos</Label><Input id="cad-suinos" name="num_suinos" type="number" min={0} max={1000000} step={1} required /></div>
      <div><Label htmlFor="cad-area">Área (m²)</Label><Input id="cad-area" name="area_m2" type="number" min="0.01" max={1000000000} step="0.01" required /></div>
      <div><Label htmlFor="cad-fonte">Fonte de água</Label><Input id="cad-fonte" name="fonte_agua" placeholder="Ex.: poço artesiano" required minLength={2} maxLength={120} /></div>
      <div><Label htmlFor="cad-hidrometro">Identificação do hidrômetro</Label><Input id="cad-hidrometro" name="hidrometro_serial" required maxLength={120} /></div>
    </div></fieldset>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    <Button className="w-full btn-primary" disabled={busy}>{busy ? "Criando conta…" : "Criar minha conta"}</Button>
    <p className="text-sm text-center">Já tem uma conta? <Link to="/login" className="text-emerald-700 font-semibold">Entrar</Link></p>
  </form></main>;
}

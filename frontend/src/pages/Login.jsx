import { useState } from "react";
import { Link, Navigate, useNavigate, useLocation } from "react-router-dom";
import { homeFor, useAuth } from "../lib/auth";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
export default function Login() {
  const { user, login, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  if (loading) return <p className="p-10">Verificando acesso…</p>;
  if (user) return <Navigate to={homeFor(user)} replace />;
  async function submit(e) {
    e.preventDefault(); setBusy(true); setError("");
    const form = new FormData(e.currentTarget);
    try { navigate(homeFor(await login(form.get("email"), form.get("password"))), { replace: true }); }
    catch (err) { setError(typeof err.response?.data?.detail === "string" ? err.response.data.detail : "Não foi possível entrar. Verifique a conexão e os dados informados."); }
    finally { setBusy(false); }
  }
  return <main className="max-w-md mx-auto px-5 py-16"><form onSubmit={submit} className="bg-white rounded-2xl border p-8 space-y-5 shadow-sm">
    <div><h1 className="text-3xl font-bold text-slate-900">Acesse sua conta</h1><p className="text-slate-500 mt-3">Acompanhe sua fazenda ou a gestão da prefeitura.</p></div>
    {location.state?.cadastro && <p role="status" className="text-emerald-700">Conta criada com sucesso! Entre para acessar sua fazenda.</p>}
    <div><Label htmlFor="email">E-mail</Label><Input id="email" name="email" type="email" defaultValue={location.state?.email || ""} autoComplete="username" required /></div>
    <div><Label htmlFor="password">Senha</Label><Input id="password" name="password" type="password" autoComplete="current-password" required /></div>
    {error && <p role="alert" className="text-red-700 text-sm">{error}</p>}
    <Button type="submit" className="w-full btn-primary" disabled={busy}>{busy ? "Entrando…" : "Entrar"}</Button>
    <Link className="block text-sm text-emerald-700" to="/recuperar">Esqueci minha senha</Link>
    <div className="border-t pt-4 text-center"><p className="text-sm text-slate-500 mb-3">Ainda não tem uma conta?</p><Button asChild variant="outline" className="w-full"><Link to="/cadastro">Criar conta</Link></Button></div>
  </form></main>;
}

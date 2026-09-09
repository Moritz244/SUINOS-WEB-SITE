import { Link } from "react-router-dom";
import { Droplets } from "lucide-react";
import { useAuth, homeFor } from "../lib/auth";
import { toast } from "sonner";
export function Header() {
  const { user, logout } = useAuth();
  return <header className="sticky top-0 z-40 bg-white border-b border-slate-200" data-testid="app-header">
    <div className="max-w-7xl mx-auto px-4 min-h-16 py-3 flex flex-wrap items-center justify-between gap-3">
      <Link to="/" className="flex items-center gap-2 font-bold text-xl"><Droplets className="text-emerald-600" /> AquaSuíno</Link>
      <nav className="flex items-center gap-4 text-sm">
        {user ? <><Link to={homeFor(user)} className="font-semibold text-emerald-700">Painel</Link>{user.role === "prefeitura" && <Link to="/prefeitura/contas">Contas</Link>}<Link to="/conta">Minha conta</Link><button onClick={() => logout().catch(() => toast.error("Não foi possível sair. Tente novamente."))}>Sair</button></> : <Link to="/login" className="font-semibold text-emerald-700">Entrar</Link>}
      </nav>
    </div>
  </header>;
}

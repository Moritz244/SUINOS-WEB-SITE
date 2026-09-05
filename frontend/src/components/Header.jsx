import { Link, useLocation, useNavigate } from "react-router-dom";
import { Droplets, Tractor, Building2, Landmark, Home } from "lucide-react";

const roles = [
  { id: "produtor", label: "Produtor", icon: Tractor, path: "/produtor", color: "emerald" },
  { id: "frivatti", label: "Frivatti", icon: Building2, path: "/frivatti", color: "sky" },
  { id: "prefeitura", label: "Prefeitura", icon: Landmark, path: "/prefeitura", color: "amber" },
];

export function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const isLanding = location.pathname === "/";

  return (
    <header className="sticky top-0 z-40 glass border-b border-slate-200/60" data-testid="app-header">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group" data-testid="brand-home-link">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-sky-500 flex items-center justify-center shadow-md">
            <Droplets className="w-5 h-5 text-white" strokeWidth={2.5} />
          </div>
          <div className="font-display font-extrabold text-lg tracking-tight">
            Aqua<span className="text-emerald-600">Suíno</span>
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-1 bg-slate-100/70 rounded-full p-1" data-testid="role-selector">
          <button
            onClick={() => navigate("/")}
            data-testid="role-selector-home"
            className={`px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-1.5 transition-colors ${
              isLanding ? "bg-white shadow text-slate-900" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Home className="w-4 h-4" /> Início
          </button>
          {roles.map((r) => {
            const active = location.pathname.startsWith(r.path);
            const Icon = r.icon;
            return (
              <button
                key={r.id}
                onClick={() => navigate(r.path)}
                data-testid={`role-selector-${r.id}`}
                className={`px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-1.5 transition-colors ${
                  active ? "bg-white shadow text-slate-900" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Icon className="w-4 h-4" /> {r.label}
              </button>
            );
          })}
        </nav>

        <div className="md:hidden">
          <select
            data-testid="role-selector-mobile"
            value={location.pathname}
            onChange={(e) => navigate(e.target.value)}
            className="rounded-full bg-white border border-slate-200 px-3 py-1.5 text-sm"
          >
            <option value="/">Início</option>
            <option value="/produtor">Produtor</option>
            <option value="/frivatti">Frivatti</option>
            <option value="/prefeitura">Prefeitura</option>
          </select>
        </div>
      </div>
    </header>
  );
}

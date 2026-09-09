import { createContext, useContext, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "./api";
const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);
export const homeFor = user => `/${user.role}`;
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    api.get("/auth/me").then(r => setUser(r.data)).catch(e => {
      if (e.response?.status !== 401) setError("Não foi possível conectar ao servidor. Recarregue a página para tentar novamente.");
    }).finally(() => setLoading(false));
    const expired = () => setUser(null);
    window.addEventListener("session-expired", expired);
    return () => window.removeEventListener("session-expired", expired);
  }, []);
  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    setError(""); setUser(data); return data;
  };
  const logout = async () => { await api.post("/auth/logout"); setUser(null); };
  return <AuthContext.Provider value={{ user, loading, error, login, logout, endSession: () => setUser(null) }}>{children}</AuthContext.Provider>;
}
export function Protected({ roles, children }) {
  const { user, loading, error } = useAuth();
  if (loading) return <p className="p-10" role="status">Verificando acesso…</p>;
  if (error) return <p className="p-10 text-red-700" role="alert">{error}</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) return <Navigate to={homeFor(user)} replace />;
  return children;
}

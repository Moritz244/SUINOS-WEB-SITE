import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Header } from "@/components/Header";
import { AuthProvider, Protected } from "@/lib/auth";
import Login from "@/pages/Login";
import Cadastro from "@/pages/Cadastro";
import Conta from "@/pages/Conta";
import Usuarios from "@/pages/Usuarios";
import Landing from "@/pages/Landing";
import Demonstracao from "@/pages/Demonstracao";
import ProdutorDashboard from "@/pages/ProdutorDashboard";
import FrivattiDashboard from "@/pages/FrivattiDashboard";
import PrefeituraDashboard from "@/pages/PrefeituraDashboard";
import { Toaster } from "@/components/ui/sonner";

function App() {
  return (
    <div className="App min-h-screen bg-[#F8FAFC]">
      <BrowserRouter>
        <AuthProvider>
        <Header />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/demonstracao" element={<Demonstracao />} />
          <Route path="/login" element={<Login />} />
          <Route path="/cadastro" element={<Cadastro />} />
          <Route path="/recuperar" element={<Conta recovery />} />
          <Route path="/conta" element={<Protected roles={["produtor", "prefeitura", "frivatti"]}><Conta /></Protected>} />
          <Route path="/prefeitura/contas" element={<Protected roles={["prefeitura"]}><Usuarios /></Protected>} />
          <Route path="/produtor" element={<Protected roles={["produtor"]}><ProdutorDashboard /></Protected>} />
          <Route path="/prefeitura/propriedades/:propId" element={<Protected roles={["prefeitura"]}><ProdutorDashboard /></Protected>} />
          <Route path="/frivatti" element={<Protected roles={["frivatti"]}><FrivattiDashboard /></Protected>} />
          <Route path="/prefeitura" element={<Protected roles={["prefeitura"]}><PrefeituraDashboard /></Protected>} />
        </Routes>
        <Toaster position="top-right" />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;

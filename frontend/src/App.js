import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Header } from "@/components/Header";
import Landing from "@/pages/Landing";
import ProdutorDashboard from "@/pages/ProdutorDashboard";
import FrivattiDashboard from "@/pages/FrivattiDashboard";
import PrefeituraDashboard from "@/pages/PrefeituraDashboard";
import { Toaster } from "@/components/ui/sonner";

function App() {
  return (
    <div className="App min-h-screen bg-[#F8FAFC]">
      <BrowserRouter>
        <Header />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/produtor" element={<ProdutorDashboard />} />
          <Route path="/frivatti" element={<FrivattiDashboard />} />
          <Route path="/prefeitura" element={<PrefeituraDashboard />} />
        </Routes>
        <Toaster position="top-right" />
      </BrowserRouter>
    </div>
  );
}

export default App;

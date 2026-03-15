import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "@/contexts/AuthContext";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Ocorrencias from "./pages/Ocorrencias";
import OcorrenciaForm from "./pages/OcorrenciaForm";
import Colaboradores from "./pages/Colaboradores";
import Equipamentos from "./pages/Equipamentos";
import Historico from "./pages/Historico";
import ResumoMensal from "./pages/ResumoMensal";
import Automacoes from "./pages/Automacoes";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/ocorrencias" element={<Ocorrencias />} />
            <Route path="/ocorrencias/nova" element={<OcorrenciaForm />} />
            <Route path="/ocorrencias/:id" element={<OcorrenciaForm />} />
            <Route path="/colaboradores" element={<Colaboradores />} />
            <Route path="/equipamentos" element={<Equipamentos />} />
            <Route path="/historico" element={<Historico />} />
            <Route path="/resumo-mensal" element={<ResumoMensal />} />
            <Route path="/automacoes" element={<Automacoes />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;

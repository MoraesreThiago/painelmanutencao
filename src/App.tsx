import { lazy, Suspense } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import Login from "./pages/Login";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Ocorrencias = lazy(() => import("./pages/Ocorrencias"));
const OcorrenciaForm = lazy(() => import("./pages/OcorrenciaForm"));
const Colaboradores = lazy(() => import("./pages/Colaboradores"));
const GerenciarUsuarios = lazy(() => import("./pages/GerenciarUsuarios"));
const Equipamentos = lazy(() => import("./pages/Equipamentos"));
const Historico = lazy(() => import("./pages/Historico"));
const ResumoMensal = lazy(() => import("./pages/ResumoMensal"));
const Automacoes = lazy(() => import("./pages/Automacoes"));
const MotoresEletricos = lazy(() => import("./pages/MotoresEletricos"));
const MotorEletricoForm = lazy(() => import("./pages/MotorEletricoForm"));
const NotFound = lazy(() => import("./pages/NotFound"));

const queryClient = new QueryClient();

const PageLoader = () => (
  <div className="flex items-center justify-center min-h-[60vh]">
    <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
  </div>
);

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/login" element={<Login />} />

              <Route element={<ProtectedRoute />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/ocorrencias" element={<Ocorrencias />} />
                <Route path="/ocorrencias/nova" element={<OcorrenciaForm />} />
                <Route path="/ocorrencias/:id" element={<OcorrenciaForm />} />
                <Route path="/colaboradores" element={<Colaboradores />} />
                <Route path="/usuarios" element={<GerenciarUsuarios />} />
                <Route path="/equipamentos" element={<Equipamentos />} />
                <Route path="/historico" element={<Historico />} />
                <Route path="/resumo-mensal" element={<ResumoMensal />} />
                <Route path="/automacoes" element={<Automacoes />} />
                <Route path="/motores-eletricos" element={<MotoresEletricos />} />
                <Route path="/motores-eletricos/novo" element={<MotorEletricoForm />} />
                <Route path="/motores-eletricos/:id" element={<MotorEletricoForm />} />
              </Route>

              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;

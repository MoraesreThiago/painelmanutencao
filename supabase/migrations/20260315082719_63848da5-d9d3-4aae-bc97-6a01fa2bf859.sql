
-- Enum for roles
CREATE TYPE public.app_role AS ENUM ('administrador', 'manutencao_eletrica', 'manutencao_mecanica');

-- User roles table
CREATE TABLE public.user_roles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  role app_role NOT NULL,
  UNIQUE (user_id, role)
);
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

-- Security definer function for role checking
CREATE OR REPLACE FUNCTION public.has_role(_user_id uuid, _role app_role)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.user_roles WHERE user_id = _user_id AND role = _role
  )
$$;

-- Profiles table
CREATE TABLE public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  nome text,
  email text,
  perfil text,
  area text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Colaboradores table
CREATE TABLE public.colaboradores (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nome text NOT NULL,
  area text NOT NULL,
  turno text NOT NULL,
  cargo text,
  status text DEFAULT 'Ativo',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
ALTER TABLE public.colaboradores ENABLE ROW LEVEL SECURITY;

-- Equipamentos table
CREATE TABLE public.equipamentos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tag text UNIQUE,
  equipamento text NOT NULL,
  local text,
  area text,
  status text DEFAULT 'Ativo',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
ALTER TABLE public.equipamentos ENABLE ROW LEVEL SECURITY;

-- Ocorrencias table
CREATE TABLE public.ocorrencias (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  data_ocorrencia date NOT NULL,
  horario text NOT NULL,
  turno text NOT NULL,
  colaborador_id uuid REFERENCES public.colaboradores(id),
  tag text,
  equipamento text,
  local text,
  area text NOT NULL,
  tipo_ocorrencia text,
  descricao text NOT NULL,
  status text DEFAULT 'Pendente',
  houve_parada boolean DEFAULT false,
  tipo_parada text,
  tempo_parada interval,
  gerar_os boolean DEFAULT false,
  prioridade_os text,
  observacao_os text,
  tipo_manutencao_os text,
  numero_os text,
  status_integracao_os text DEFAULT 'Nao solicitada',
  created_by uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
ALTER TABLE public.ocorrencias ENABLE ROW LEVEL SECURITY;

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
CREATE TRIGGER update_colaboradores_updated_at BEFORE UPDATE ON public.colaboradores FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
CREATE TRIGGER update_equipamentos_updated_at BEFORE UPDATE ON public.equipamentos FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
CREATE TRIGGER update_ocorrencias_updated_at BEFORE UPDATE ON public.ocorrencias FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- Indexes
CREATE INDEX idx_ocorrencias_data ON public.ocorrencias(data_ocorrencia);
CREATE INDEX idx_ocorrencias_area ON public.ocorrencias(area);
CREATE INDEX idx_ocorrencias_status ON public.ocorrencias(status);
CREATE INDEX idx_ocorrencias_tag ON public.ocorrencias(tag);
CREATE INDEX idx_ocorrencias_equipamento ON public.ocorrencias(equipamento);
CREATE INDEX idx_equipamentos_tag ON public.equipamentos(tag);
CREATE INDEX idx_colaboradores_area ON public.colaboradores(area);

-- RLS Policies for user_roles
CREATE POLICY "Users can read own roles" ON public.user_roles FOR SELECT TO authenticated USING (user_id = auth.uid());
CREATE POLICY "Admins can manage all roles" ON public.user_roles FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'administrador'));

-- RLS Policies for profiles
CREATE POLICY "Authenticated can read profiles" ON public.profiles FOR SELECT TO authenticated USING (true);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE TO authenticated USING (id = auth.uid());
CREATE POLICY "Users can insert own profile" ON public.profiles FOR INSERT TO authenticated WITH CHECK (id = auth.uid());

-- RLS Policies for colaboradores
CREATE POLICY "Authenticated can read colaboradores" ON public.colaboradores FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated can insert colaboradores" ON public.colaboradores FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Authenticated can update colaboradores" ON public.colaboradores FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Admins can delete colaboradores" ON public.colaboradores FOR DELETE TO authenticated USING (public.has_role(auth.uid(), 'administrador'));

-- RLS Policies for equipamentos
CREATE POLICY "Authenticated can read equipamentos" ON public.equipamentos FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated can insert equipamentos" ON public.equipamentos FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Authenticated can update equipamentos" ON public.equipamentos FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Admins can delete equipamentos" ON public.equipamentos FOR DELETE TO authenticated USING (public.has_role(auth.uid(), 'administrador'));

-- RLS Policies for ocorrencias
CREATE POLICY "Authenticated can read ocorrencias" ON public.ocorrencias FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated can insert ocorrencias" ON public.ocorrencias FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Authenticated can update ocorrencias" ON public.ocorrencias FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Admins can delete ocorrencias" ON public.ocorrencias FOR DELETE TO authenticated USING (public.has_role(auth.uid(), 'administrador'));

-- Seed equipamentos
INSERT INTO public.equipamentos (tag, equipamento, local, area) VALUES
('EQ-001', 'Motor Bomba Principal', 'Sala de Bombas', 'Elétrica'),
('EQ-002', 'Compressor de Ar', 'Utilidades', 'Mecânica'),
('EQ-003', 'Painel Elétrico CCM-01', 'Subestação', 'Elétrica'),
('EQ-004', 'Esteira Transportadora L1', 'Linha 1', 'Mecânica'),
('EQ-005', 'Inversor de Frequência IF-01', 'Linha 1', 'Elétrica'),
('EQ-006', 'Caldeira a Vapor CV-01', 'Utilidades', 'Mecânica'),
('EQ-007', 'Transformador TR-01', 'Subestação', 'Elétrica'),
('EQ-008', 'Prensa Hidráulica PH-01', 'Linha 2', 'Mecânica'),
('EQ-009', 'Sensor de Nível SN-01', 'Tanques', 'Elétrica'),
('EQ-010', 'Redutor de Velocidade RV-01', 'Linha 1', 'Mecânica');

-- Seed colaboradores
INSERT INTO public.colaboradores (nome, area, turno, cargo, status) VALUES
('Carlos Silva', 'Elétrica', 'A', 'Eletricista', 'Ativo'),
('João Souza', 'Mecânica', 'A', 'Mecânico', 'Ativo'),
('Maria Santos', 'Elétrica', 'B', 'Eletricista', 'Ativo'),
('Pedro Oliveira', 'Mecânica', 'B', 'Mecânico', 'Ativo'),
('Ana Costa', 'Elétrica', 'C', 'Instrumentista', 'Ativo'),
('Roberto Lima', 'Mecânica', 'C', 'Mecânico', 'Ativo'),
('Fernanda Dias', 'Elétrica', 'D', 'Eletricista', 'Ativo'),
('Lucas Martins', 'Mecânica', 'D', 'Mecânico', 'Ativo'),
('Patricia Rocha', 'Elétrica', 'ADM', 'Supervisor Elétrica', 'Ativo'),
('Ricardo Ferreira', 'Mecânica', 'ADM', 'Supervisor Mecânica', 'Ativo');

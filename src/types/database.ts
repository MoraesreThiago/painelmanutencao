export interface Profile {
  id: string;
  nome: string | null;
  email: string | null;
  perfil: string | null;
  area: string | null;
  created_at: string;
  updated_at: string;
}

export interface Colaborador {
  id: string;
  nome: string;
  area: string;
  turno: string;
  cargo: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Equipamento {
  id: string;
  tag: string | null;
  equipamento: string;
  local: string | null;
  area: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Ocorrencia {
  id: string;
  data_ocorrencia: string;
  horario: string;
  turno: string;
  colaborador_id: string | null;
  tag: string | null;
  equipamento: string | null;
  local: string | null;
  area: string;
  tipo_ocorrencia: string | null;
  descricao: string;
  status: string;
  houve_parada: boolean;
  tipo_parada: string | null;
  tempo_parada: string | null;
  gerar_os: boolean;
  prioridade_os: string | null;
  observacao_os: string | null;
  tipo_manutencao_os: string | null;
  numero_os: string | null;
  status_integracao_os: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  colaboradores?: Colaborador;
}

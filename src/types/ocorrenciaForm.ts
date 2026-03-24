import type { Tables } from '@/integrations/supabase/types';

// ─── Supabase view type ──────────────────────────────────────────────────────
export type EquipamentoView = Tables<'vw_equipamentos_app'>;

// ─── Form state ──────────────────────────────────────────────────────────────
export interface OcorrenciaFormState {
  data_ocorrencia: string;
  horario: string;
  turno: string;
  colaborador_id: string;
  tag: string;
  equipamento: string;
  local: string;
  area: string;
  tipo_ocorrencia: string;
  descricao: string;
  status: string;
  houve_parada: boolean;
  tipo_parada: string;
  tempo_parada: string;
  gerar_os: boolean;
  prioridade_os: string;
  observacao_os: string;
  tipo_manutencao_os: string;
  area_responsavel: string;
}

// ─── Payload sent to Supabase ────────────────────────────────────────────────
export interface OcorrenciaPayload {
  data_ocorrencia: string;
  horario: string;
  turno: string;
  colaborador_id: string | null;
  tag: string;
  equipamento: string;
  local: string;
  area: string;
  tipo_ocorrencia: string;
  descricao: string;
  status: string;
  houve_parada: boolean;
  tipo_parada: string | null;
  tempo_parada: string | null;
  gerar_os: boolean;
  prioridade_os: string | null;
  observacao_os: string | null;
  tipo_manutencao_os: string | null;
  area_responsavel: string | null;
  created_by?: string;
}

// ─── Validation ──────────────────────────────────────────────────────────────
export interface ValidationError {
  field: string;
  message: string;
}

export function validateOcorrenciaForm(form: OcorrenciaFormState): ValidationError | null {
  if (!form.colaborador_id) return { field: 'colaborador_id', message: 'Colaborador é obrigatório' };
  if (!form.tipo_ocorrencia) return { field: 'tipo_ocorrencia', message: 'Tipo de Ocorrência é obrigatório' };
  if (!form.descricao.trim()) return { field: 'descricao', message: 'Descrição é obrigatória' };
  if (form.descricao.trim().length < 20) return { field: 'descricao', message: 'Descrição deve ter no mínimo 20 caracteres' };
  if (form.houve_parada && form.tempo_parada && isNaN(Number(form.tempo_parada))) {
    return { field: 'tempo_parada', message: 'Tempo de parada deve ser um número válido' };
  }
  return null;
}

export function buildPayload(form: OcorrenciaFormState, userId?: string): OcorrenciaPayload {
  return {
    data_ocorrencia: form.data_ocorrencia,
    horario: form.horario,
    turno: form.turno,
    colaborador_id: form.colaborador_id || null,
    tag: form.tag,
    equipamento: form.equipamento,
    local: form.local,
    area: form.area,
    tipo_ocorrencia: form.tipo_ocorrencia,
    descricao: form.descricao,
    status: form.status,
    houve_parada: form.houve_parada,
    tipo_parada: form.houve_parada ? form.tipo_parada : null,
    tempo_parada: form.houve_parada && form.tempo_parada ? `${form.tempo_parada} minutes` : null,
    gerar_os: form.gerar_os,
    prioridade_os: form.gerar_os ? form.prioridade_os : null,
    observacao_os: form.gerar_os ? form.observacao_os : null,
    tipo_manutencao_os: form.gerar_os ? form.tipo_manutencao_os : null,
    area_responsavel: form.area_responsavel || null,
    ...(userId ? { created_by: userId } : {}),
  };
}

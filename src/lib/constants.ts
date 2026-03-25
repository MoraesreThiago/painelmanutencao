/** Shared constants used across multiple pages and components */

// ─── Status colors (used in Dashboard, Ocorrencias, Historico) ──────────────
export const STATUS_COLORS: Record<string, string> = {
  Pendente: 'bg-status-pendente text-primary-foreground',
  Liberado: 'bg-status-liberado text-primary-foreground',
  'Em andamento': 'bg-status-andamento text-primary-foreground',
  Realizada: 'bg-status-realizada text-primary-foreground',
};

// ─── Areas ──────────────────────────────────────────────────────────────────
export const AREAS = ['Elétrica', 'Mecânica', 'Instrumentação'] as const;
export type Area = (typeof AREAS)[number];

// ─── Turnos ─────────────────────────────────────────────────────────────────
export const TURNOS = ['A', 'B', 'C', 'D', 'ADM'] as const;
export type Turno = (typeof TURNOS)[number];

// ─── Horarios ───────────────────────────────────────────────────────────────
export const HORARIOS = ['Dia', 'Amanhecida'] as const;

// ─── Turno schedule constants ───────────────────────────────────────────────
export const DIA_SEQUENCE = ['A', 'D', 'B', 'C'] as const;
export const AMAN_SEQUENCE = ['B', 'C', 'A', 'D'] as const;
export const REFERENCE_DATE = new Date(2026, 1, 18);

// ─── Perfil ↔ Área mapping ─────────────────────────────────────────────────
export const PERFIL_AREA_MAP: Record<string, string> = {
  manutencao_eletrica: 'Elétrica',
  manutencao_mecanica: 'Mecânica',
  manutencao_instrumentacao: 'Instrumentação',
  lider_eletrica: 'Elétrica',
  lider_mecanica: 'Mecânica',
  lider_instrumentacao: 'Instrumentação',
  supervisor_eletrica: 'Elétrica',
  supervisor_mecanica: 'Mecânica',
  supervisor_instrumentacao: 'Instrumentação',
};

// ─── Creatable perfis (for user management) ─────────────────────────────────
export const CREATABLE_PERFIS = [
  { value: 'supervisor_eletrica', label: 'Supervisor Elétrica' },
  { value: 'supervisor_mecanica', label: 'Supervisor Mecânica' },
  { value: 'supervisor_instrumentacao', label: 'Supervisor Instrumentação' },
  { value: 'lider_eletrica', label: 'Líder Elétrica' },
  { value: 'lider_mecanica', label: 'Líder Mecânica' },
  { value: 'lider_instrumentacao', label: 'Líder Instrumentação' },
  { value: 'manutencao_eletrica', label: 'Manutenção Elétrica' },
  { value: 'manutencao_mecanica', label: 'Manutenção Mecânica' },
  { value: 'manutencao_instrumentacao', label: 'Manutenção Instrumentação' },
] as const;

// ─── Active/Inactive status badge class ─────────────────────────────────────
export const ACTIVE_BADGE_CLASS = 'bg-status-realizada text-primary-foreground';
export const INACTIVE_BADGE_CLASS = 'bg-muted text-muted-foreground';

// ─── Pagination ─────────────────────────────────────────────────────────────
export const DEFAULT_PAGE_SIZE = 20;

// ─── 24h edit lock (milliseconds) ──────────────────────────────────────────
export const EDIT_LOCK_MS = 24 * 60 * 60 * 1000;

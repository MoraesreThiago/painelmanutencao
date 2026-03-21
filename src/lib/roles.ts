import type { Profile } from '@/types/database';

const LEADER_ROLES = ['lider_eletrica', 'lider_mecanica', 'lider_instrumentacao'];
const SUPERVISOR_ROLES = ['supervisor_eletrica', 'supervisor_mecanica', 'supervisor_instrumentacao'];
const ELEVATED_ROLES = ['administrador', ...LEADER_ROLES, ...SUPERVISOR_ROLES];

export const isAdmin = (profile: Profile | null) =>
  profile?.perfil === 'administrador';

export const isLeader = (profile: Profile | null) =>
  LEADER_ROLES.includes(profile?.perfil || '');

export const isSupervisor = (profile: Profile | null) =>
  SUPERVISOR_ROLES.includes(profile?.perfil || '');

/** Admin, líder ou supervisor */
export const isLeaderOrAbove = (profile: Profile | null) =>
  ELEVATED_ROLES.includes(profile?.perfil || '');

/** Pode gerenciar colaboradores (admin ou líder/supervisor da área) */
export const canManageColaboradores = (profile: Profile | null) =>
  isAdmin(profile) || isLeader(profile) || isSupervisor(profile);

/** Pode editar/excluir ocorrências sem limite de 24h */
export const canEditWithoutTimeLimit = (profile: Profile | null) =>
  isAdmin(profile) || isLeader(profile) || isSupervisor(profile);

/** Perfil de elétrica (qualquer nível) */
export const isEletrica = (profile: Profile | null) =>
  profile?.area === 'Elétrica';

export const getRoleLabel = (perfil: string | null): string => {
  const labels: Record<string, string> = {
    administrador: 'Administrador',
    manutencao_eletrica: 'Manutenção Elétrica',
    manutencao_mecanica: 'Manutenção Mecânica',
    manutencao_instrumentacao: 'Manutenção Instrumentação',
    lider_eletrica: 'Líder Elétrica',
    lider_mecanica: 'Líder Mecânica',
    lider_instrumentacao: 'Líder Instrumentação',
    supervisor_eletrica: 'Supervisor Elétrica',
    supervisor_mecanica: 'Supervisor Mecânica',
    supervisor_instrumentacao: 'Supervisor Instrumentação',
  };
  return labels[perfil || ''] || perfil || '';
};

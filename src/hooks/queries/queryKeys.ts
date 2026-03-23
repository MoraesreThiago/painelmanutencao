/** Centralized query key factory for cache management */
export const queryKeys = {
  // Dashboard
  dashboard: {
    turnoOcorrencias: (turno: string, horario: string, dates: string[]) =>
      ['dashboard', 'turno-ocorrencias', turno, horario, ...dates] as const,
  },

  // Ocorrencias
  ocorrencias: {
    all: ['ocorrencias'] as const,
    list: (filters: object) =>
      ['ocorrencias', 'list', filters] as const,
  },

  // Equipamentos
  equipamentos: {
    all: ['equipamentos'] as const,
    list: (filters: Record<string, string | number>) =>
      ['equipamentos', 'list', filters] as const,
    full: ['equipamentos', 'full'] as const,
  },

  // Colaboradores
  colaboradores: {
    all: ['colaboradores'] as const,
    list: ['colaboradores', 'list'] as const,
    active: ['colaboradores', 'active'] as const,
  },
} as const;

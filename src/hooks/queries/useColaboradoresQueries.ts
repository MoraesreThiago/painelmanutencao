import { useQuery, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import type { Colaborador } from '@/types/database';
import { queryKeys } from './queryKeys';

// ─── All colaboradores ──────────────────────────────────────────────────────

async function fetchColaboradores(): Promise<Colaborador[]> {
  const { data, error } = await supabase
    .from('colaboradores')
    .select('*')
    .order('nome');

  if (error) throw error;
  return (data ?? []) as Colaborador[];
}

export function useColaboradores() {
  return useQuery({
    queryKey: queryKeys.colaboradores.list,
    queryFn: fetchColaboradores,
    staleTime: 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}

// ─── Active only (for forms) ────────────────────────────────────────────────

async function fetchActiveColaboradores(): Promise<Colaborador[]> {
  const { data, error } = await supabase
    .from('colaboradores')
    .select('*')
    .eq('status', 'Ativo')
    .order('nome');

  if (error) throw error;
  return (data ?? []) as Colaborador[];
}

export function useActiveColaboradores() {
  return useQuery({
    queryKey: queryKeys.colaboradores.active,
    queryFn: fetchActiveColaboradores,
    staleTime: 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}

export function useInvalidateColaboradores() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: queryKeys.colaboradores.all });
}

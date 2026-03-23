import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import type { Ocorrencia } from '@/types/database';
import { queryKeys } from './queryKeys';

interface TurnoOcorrenciasParams {
  turno: string;
  horario: string;
  dates: string[];   // for "in" filter
  exactDate?: string; // for "eq" filter (overrides dates)
}

async function fetchTurnoOcorrencias(params: TurnoOcorrenciasParams): Promise<Ocorrencia[]> {
  let query = supabase
    .from('ocorrencias')
    .select('*, colaboradores(nome)')
    .eq('turno', params.turno)
    .eq('horario', params.horario)
    .order('created_at', { ascending: false })
    .limit(10);

  if (params.exactDate) {
    query = query.eq('data_ocorrencia', params.exactDate);
  } else {
    query = query.in('data_ocorrencia', params.dates);
  }

  const { data, error } = await query;
  if (error) throw error;
  return (data ?? []) as Ocorrencia[];
}

export function useTurnoOcorrencias(params: TurnoOcorrenciasParams) {
  return useQuery({
    queryKey: queryKeys.dashboard.turnoOcorrencias(
      params.turno,
      params.horario,
      params.exactDate ? [params.exactDate] : params.dates,
    ),
    queryFn: () => fetchTurnoOcorrencias(params),
    staleTime: 2 * 60 * 1000,   // 2 min
    gcTime: 5 * 60 * 1000,      // 5 min
  });
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import type { Ocorrencia } from '@/types/database';
import { queryKeys } from './queryKeys';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface OcorrenciasFilters {
  status: string;
  area: string;
  turno: string;
  search: string;
  page: number;
}

interface OcorrenciasResult {
  data: Ocorrencia[];
  totalCount: number;
}

const PAGE_SIZE = 20;

// ─── Fetch ───────────────────────────────────────────────────────────────────

async function fetchOcorrencias(filters: OcorrenciasFilters): Promise<OcorrenciasResult> {
  const from = filters.page * PAGE_SIZE;
  const to = from + PAGE_SIZE - 1;

  let countQuery = supabase
    .from('ocorrencias')
    .select('*', { count: 'exact', head: true });

  let dataQuery = supabase
    .from('ocorrencias')
    .select('*, colaboradores(nome)')
    .order('data_ocorrencia', { ascending: false })
    .order('created_at', { ascending: false })
    .range(from, to);

  if (filters.status !== 'todos') {
    countQuery = countQuery.eq('status', filters.status);
    dataQuery = dataQuery.eq('status', filters.status);
  }
  if (filters.area !== 'todos') {
    countQuery = countQuery.eq('area', filters.area);
    dataQuery = dataQuery.eq('area', filters.area);
  }
  if (filters.turno !== 'todos') {
    countQuery = countQuery.eq('turno', filters.turno);
    dataQuery = dataQuery.eq('turno', filters.turno);
  }
  if (filters.search.trim()) {
    const s = `%${filters.search.trim()}%`;
    const orFilter = `tag.ilike.${s},equipamento.ilike.${s},descricao.ilike.${s},area.ilike.${s}`;
    countQuery = countQuery.or(orFilter);
    dataQuery = dataQuery.or(orFilter);
  }

  const [countRes, dataRes] = await Promise.all([countQuery, dataQuery]);

  if (countRes.error) throw countRes.error;
  if (dataRes.error) throw dataRes.error;

  return {
    data: (dataRes.data ?? []) as Ocorrencia[],
    totalCount: countRes.count ?? 0,
  };
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export function useOcorrencias(filters: OcorrenciasFilters) {
  return useQuery({
    queryKey: queryKeys.ocorrencias.list(filters),
    queryFn: () => fetchOcorrencias(filters),
    staleTime: 30 * 1000,   // 30s
    gcTime: 5 * 60 * 1000,  // 5 min
    placeholderData: (prev) => prev, // keep previous data while loading next page
  });
}

export { PAGE_SIZE as OCORRENCIAS_PAGE_SIZE };

// ─── Mutations ───────────────────────────────────────────────────────────────

export function useInvalidateOcorrencias() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: queryKeys.ocorrencias.all });
    qc.invalidateQueries({ queryKey: ['dashboard'] });
  };
}

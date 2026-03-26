import { useQuery, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import type { Tables } from '@/integrations/supabase/types';
import { queryKeys } from './queryKeys';

type EquipamentoView = Tables<'vw_equipamentos_app'>;

const PAGE_SIZE = 20;

// ─── Paginated list (for Equipamentos page) ─────────────────────────────────

interface EquipamentosFilters {
  search: string;
  page: number;
}

interface EquipamentosResult {
  data: EquipamentoView[];
  totalCount: number;
}

async function fetchEquipamentosPaginated(filters: EquipamentosFilters): Promise<EquipamentosResult> {
  const from = filters.page * PAGE_SIZE;
  const to = from + PAGE_SIZE - 1;

  let countQuery = supabase
    .from('vw_equipamentos_app')
    .select('*', { count: 'exact', head: true });

  let dataQuery = supabase
    .from('vw_equipamentos_app')
    .select('*')
    .order('tag', { ascending: true })
    .range(from, to);

  if (filters.search.trim()) {
    const s = `%${filters.search.trim()}%`;
    const orFilter = `tag.ilike.${s},equipamento.ilike.${s}`;
    countQuery = countQuery.or(orFilter);
    dataQuery = dataQuery.or(orFilter);
  }

  const [countRes, dataRes] = await Promise.all([countQuery, dataQuery]);
  if (countRes.error) throw countRes.error;
  if (dataRes.error) throw dataRes.error;

  return {
    data: (dataRes.data ?? []) as EquipamentoView[],
    totalCount: countRes.count ?? 0,
  };
}

export function useEquipamentosPaginated(filters: EquipamentosFilters) {
  return useQuery({
    queryKey: queryKeys.equipamentos.list(filters),
    queryFn: () => fetchEquipamentosPaginated(filters),
    staleTime: 60 * 1000,
    gcTime: 5 * 60 * 1000,
    placeholderData: (prev) => prev,
  });
}

export { PAGE_SIZE as EQUIPAMENTOS_PAGE_SIZE };

export function useInvalidateEquipamentos() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: queryKeys.equipamentos.all });
}

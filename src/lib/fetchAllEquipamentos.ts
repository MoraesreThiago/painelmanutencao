import { supabase } from '@/integrations/supabase/client';
import type { Equipamento } from '@/types/database';

const PAGE_SIZE = 1000;

export const fetchAllEquipamentos = async () => {
  const items: Equipamento[] = [];

  for (let from = 0; ; from += PAGE_SIZE) {
    const to = from + PAGE_SIZE - 1;
    const { data, error } = await (supabase as any)
      .from('vw_equipamentos_consolidados')
      .select('tag, equipamento, area, status, local_exemplo, updated_at')
      .order('tag', { ascending: true })
      .range(from, to);

    if (error) {
      throw error;
    }

    const batch = (data || []).map((d: any) => ({ ...d, local: d.local_exemplo })) as Equipamento[];
    items.push(...batch);

    if (batch.length < PAGE_SIZE) {
      break;
    }
  }

  return items;
};

import { supabase } from '@/integrations/supabase/client';
import type { Equipamento } from '@/types/database';

const PAGE_SIZE = 1000;

export const fetchAllEquipamentos = async () => {
  const items: Equipamento[] = [];

  for (let from = 0; ; from += PAGE_SIZE) {
    const to = from + PAGE_SIZE - 1;
    const { data, error } = await supabase
      .from('vw_equipamentos_app')
      .select('*')
      .order('tag', { ascending: true })
      .range(from, to);

    if (error) {
      throw error;
    }

    const batch = (data ?? []) as Equipamento[];
    items.push(...batch);

    if (batch.length < PAGE_SIZE) {
      break;
    }
  }

  return items;
};

import { supabase } from '@/integrations/supabase/client';
import type { Tables } from '@/integrations/supabase/types';

type EquipamentoView = Tables<'vw_equipamentos_app'>;

const PAGE_SIZE = 1000;

export const fetchAllEquipamentos = async () => {
  const items: EquipamentoView[] = [];

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

    const batch = data ?? [];
    items.push(...batch);

    if (batch.length < PAGE_SIZE) {
      break;
    }
  }

  return items;
};

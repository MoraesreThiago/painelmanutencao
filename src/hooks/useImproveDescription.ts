import { useState, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';

export function useImproveDescription() {
  const [improving, setImproving] = useState(false);

  const improve = useCallback(async (descricao: string): Promise<string | null> => {
    if (!descricao.trim()) {
      toast.error('Digite uma descrição primeiro');
      return null;
    }

    setImproving(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const res = await fetch(
        `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/improve-description`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${session?.access_token || ''}`,
          },
          body: JSON.stringify({ descricao }),
        },
      );

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Erro ao melhorar descrição');

      if (data.improved) {
        toast.success('Descrição aprimorada pela IA!');
        return data.improved as string;
      }
      return null;
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Erro ao processar com IA');
      return null;
    } finally {
      setImproving(false);
    }
  }, []);

  return { improving, improve };
}

import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import type { EquipamentoView } from '@/types/ocorrenciaForm';

const SEARCH_LIMIT = 20;
const DEBOUNCE_MS = 300;

async function searchEquipamentos(term: string): Promise<EquipamentoView[]> {
  if (!term.trim()) return [];
  const pattern = `%${term.trim()}%`;
  const { data, error } = await supabase
    .from('vw_equipamentos_app')
    .select('*')
    .or(`tag.ilike.${pattern},equipamento.ilike.${pattern}`)
    .order('tag', { ascending: true })
    .limit(SEARCH_LIMIT);

  if (error) throw error;
  return (data ?? []) as EquipamentoView[];
}

async function searchLocais(term: string): Promise<string[]> {
  if (!term.trim()) return [];
  const pattern = `%${term.trim()}%`;
  const { data, error } = await supabase
    .from('vw_equipamentos_app')
    .select('local')
    .ilike('local', pattern)
    .limit(SEARCH_LIMIT);

  if (error) throw error;
  const unique = [...new Set((data ?? []).map(d => d.local).filter(Boolean))] as string[];
  return unique;
}

/** Debounces a value by `delay` ms. */
function useDebouncedValue(value: string, delay: number): string {
  const [debounced, setDebounced] = useState(value);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    timerRef.current = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timerRef.current);
  }, [value, delay]);

  return debounced;
}

/**
 * Debounced equipment search hook — fetches on demand with real debounce.
 */
export function useEquipamentoSearch() {
  const [tagTerm, setTagTerm] = useState('');
  const [eqTerm, setEqTerm] = useState('');
  const [localTerm, setLocalTerm] = useState('');
  const [showTagSuggestions, setShowTagSuggestions] = useState(false);
  const [showEqSuggestions, setShowEqSuggestions] = useState(false);
  const [showLocalSuggestions, setShowLocalSuggestions] = useState(false);

  const debouncedTag = useDebouncedValue(tagTerm, DEBOUNCE_MS);
  const debouncedEq = useDebouncedValue(eqTerm, DEBOUNCE_MS);
  const debouncedLocal = useDebouncedValue(localTerm, DEBOUNCE_MS);

  const tagQuery = useQuery({
    queryKey: ['eq-search', 'tag', debouncedTag],
    queryFn: () => searchEquipamentos(debouncedTag),
    enabled: debouncedTag.length > 0 && showTagSuggestions,
    gcTime: 60_000,
  });

  const eqQuery = useQuery({
    queryKey: ['eq-search', 'eq', debouncedEq],
    queryFn: () => searchEquipamentos(debouncedEq),
    enabled: debouncedEq.length > 0 && showEqSuggestions,
    gcTime: 60_000,
  });

  const localQuery = useQuery({
    queryKey: ['eq-search', 'local', debouncedLocal],
    queryFn: () => searchLocais(debouncedLocal),
    enabled: debouncedLocal.length > 0 && showLocalSuggestions,
    gcTime: 60_000,
  });

  return {
    tagTerm, setTagTerm,
    tagSuggestions: tagQuery.data ?? [],
    showTagSuggestions, setShowTagSuggestions,
    eqTerm, setEqTerm,
    eqSuggestions: eqQuery.data ?? [],
    showEqSuggestions, setShowEqSuggestions,
    localTerm, setLocalTerm,
    localSuggestions: localQuery.data ?? [],
    showLocalSuggestions, setShowLocalSuggestions,
  };
}

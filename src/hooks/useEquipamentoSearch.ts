import { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import type { EquipamentoView } from '@/types/ocorrenciaForm';

const SEARCH_LIMIT = 20;
const DEBOUNCE_MS = 250;

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

/**
 * Debounced equipment search hook — fetches on demand instead of loading all.
 */
export function useEquipamentoSearch() {
  const [tagTerm, setTagTerm] = useState('');
  const [eqTerm, setEqTerm] = useState('');
  const [localTerm, setLocalTerm] = useState('');
  const [showTagSuggestions, setShowTagSuggestions] = useState(false);
  const [showEqSuggestions, setShowEqSuggestions] = useState(false);
  const [showLocalSuggestions, setShowLocalSuggestions] = useState(false);

  // Debounced values using React Query's built-in staleTime
  const tagQuery = useQuery({
    queryKey: ['eq-search', 'tag', tagTerm],
    queryFn: () => searchEquipamentos(tagTerm),
    enabled: tagTerm.length > 0 && showTagSuggestions,
    staleTime: DEBOUNCE_MS,
    gcTime: 60_000,
  });

  const eqQuery = useQuery({
    queryKey: ['eq-search', 'eq', eqTerm],
    queryFn: () => searchEquipamentos(eqTerm),
    enabled: eqTerm.length > 0 && showEqSuggestions,
    staleTime: DEBOUNCE_MS,
    gcTime: 60_000,
  });

  const localQuery = useQuery({
    queryKey: ['eq-search', 'local', localTerm],
    queryFn: () => searchLocais(localTerm),
    enabled: localTerm.length > 0 && showLocalSuggestions,
    staleTime: DEBOUNCE_MS,
    gcTime: 60_000,
  });

  return {
    // Tag
    tagTerm, setTagTerm,
    tagSuggestions: tagQuery.data ?? [],
    showTagSuggestions, setShowTagSuggestions,
    // Equipamento
    eqTerm, setEqTerm,
    eqSuggestions: eqQuery.data ?? [],
    showEqSuggestions, setShowEqSuggestions,
    // Local
    localTerm, setLocalTerm,
    localSuggestions: localQuery.data ?? [],
    showLocalSuggestions, setShowLocalSuggestions,
  };
}

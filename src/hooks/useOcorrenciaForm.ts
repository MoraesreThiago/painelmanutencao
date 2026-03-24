import { useCallback, useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import type { OcorrenciaFormState } from '@/types/ocorrenciaForm';

// ─── Turno / horário helpers ─────────────────────────────────────────────────

function getHorarioByTime(): string {
  const now = new Date();
  const totalMin = now.getHours() * 60 + now.getMinutes();
  return totalMin >= 430 && totalMin < 1150 ? 'Dia' : 'Amanhecida';
}

function getOperationalDate(): Date {
  const now = new Date();
  const totalMin = now.getHours() * 60 + now.getMinutes();
  return totalMin >= 430
    ? new Date(now.getFullYear(), now.getMonth(), now.getDate())
    : new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
}

function getTurnoByDate(): string {
  const DIA_SEQ = ['A', 'D', 'B', 'C'];
  const NOITE_SEQ = ['B', 'C', 'A', 'D'];
  const REF_DATE = new Date(2026, 1, 18);

  const horario = getHorarioByTime();
  const opDate = getOperationalDate();
  const deltaDays = Math.round((opDate.getTime() - REF_DATE.getTime()) / 86400000);
  const steps = Math.floor(deltaDays / 2);

  const seq = horario === 'Dia' ? DIA_SEQ : NOITE_SEQ;
  let idx = steps % seq.length;
  if (idx < 0) idx += seq.length;
  return seq[idx];
}

function getDataOcorrencia(): string {
  const ref = getOperationalDate();
  return `${ref.getFullYear()}-${String(ref.getMonth() + 1).padStart(2, '0')}-${String(ref.getDate()).padStart(2, '0')}`;
}

// ─── Defaults ────────────────────────────────────────────────────────────────

function createDefaults(area: string): OcorrenciaFormState {
  return {
    data_ocorrencia: getDataOcorrencia(),
    horario: getHorarioByTime(),
    turno: getTurnoByDate(),
    colaborador_id: '',
    tag: '',
    equipamento: '',
    local: '',
    area,
    tipo_ocorrencia: '',
    descricao: '',
    status: 'Liberado',
    houve_parada: false,
    tipo_parada: '',
    tempo_parada: '',
    gerar_os: false,
    prioridade_os: '',
    observacao_os: '',
    tipo_manutencao_os: '',
    area_responsavel: '',
  };
}

// ─── Hook ────────────────────────────────────────────────────────────────────

interface UseOcorrenciaFormOptions {
  id?: string;
  profileArea?: string | null;
}

export function useOcorrenciaForm({ id, profileArea }: UseOcorrenciaFormOptions) {
  const isEdit = !!id;
  const [form, setForm] = useState<OcorrenciaFormState>(
    () => createDefaults(profileArea || 'Elétrica'),
  );
  const [tagSearch, setTagSearch] = useState('');
  const [eqSearch, setEqSearch] = useState('');
  const [localSearch, setLocalSearch] = useState('');

  // Sync area from profile on first load (profile may arrive late)
  useEffect(() => {
    if (profileArea && !isEdit) {
      setForm(prev => ({ ...prev, area: profileArea }));
    }
  }, [profileArea, isEdit]);

  // Load existing record in edit mode
  useEffect(() => {
    if (!isEdit || !id) return;
    let cancelled = false;

    const load = async () => {
      const { data } = await supabase.from('ocorrencias').select('*').eq('id', id).single();
      if (cancelled || !data) return;

      setForm({
        data_ocorrencia: data.data_ocorrencia,
        horario: data.horario,
        turno: data.turno,
        colaborador_id: data.colaborador_id || '',
        tag: data.tag || '',
        equipamento: data.equipamento || '',
        local: data.local || '',
        area: data.area,
        tipo_ocorrencia: data.tipo_ocorrencia || '',
        descricao: data.descricao,
        status: data.status || 'Pendente',
        houve_parada: data.houve_parada || false,
        tipo_parada: data.tipo_parada || '',
        tempo_parada: data.tempo_parada || '',
        gerar_os: data.gerar_os || false,
        prioridade_os: data.prioridade_os || '',
        observacao_os: data.observacao_os || '',
        tipo_manutencao_os: data.tipo_manutencao_os || '',
        area_responsavel: data.area_responsavel || '',
      });
      setTagSearch(data.tag || '');
      setEqSearch(data.equipamento || '');
      setLocalSearch(data.local || '');
    };

    load();
    return () => { cancelled = true; };
  }, [id, isEdit]);

  const setField = useCallback(<K extends keyof OcorrenciaFormState>(key: K, value: OcorrenciaFormState[K]) => {
    setForm(prev => ({ ...prev, [key]: value }));
  }, []);

  return {
    form,
    setField,
    setForm,
    isEdit,
    tagSearch,
    setTagSearch,
    eqSearch,
    setEqSearch,
    localSearch,
    setLocalSearch,
  };
}

import { useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

import { useOcorrenciaForm } from '@/hooks/useOcorrenciaForm';
import { useEquipamentoSearch } from '@/hooks/useEquipamentoSearch';
import { useImproveDescription } from '@/hooks/useImproveDescription';
import { useActiveColaboradores, useInvalidateOcorrencias } from '@/hooks/queries';
import { validateOcorrenciaForm, buildPayload } from '@/types/ocorrenciaForm';
import type { EquipamentoView } from '@/types/ocorrenciaForm';

import InformacoesGerais from '@/components/ocorrencia/InformacoesGerais';
import EquipamentoSection from '@/components/ocorrencia/EquipamentoSection';
import DescricaoSection from '@/components/ocorrencia/DescricaoSection';
import ParadaSection from '@/components/ocorrencia/ParadaSection';
import FormActions from '@/components/ocorrencia/FormActions';

const OcorrenciaForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, profile } = useAuth();
  const isAdmin = profile?.perfil === 'administrador';

  const [saving, setSaving] = useState(false);

  // ─── Hooks ───────────────────────────────────────────────────────────────
  const {
    form, setField, isEdit,
    tagSearch, setTagSearch,
    eqSearch, setEqSearch,
    localSearch, setLocalSearch,
  } = useOcorrenciaForm({ id, profileArea: profile?.area });

  const eqSearchHook = useEquipamentoSearch();
  const { improving, improve } = useImproveDescription();
  const { data: colaboradores = [] } = useActiveColaboradores();
  const invalidateOcorrencias = useInvalidateOcorrencias();

  // Sync search terms between form hook and eq search hook
  const handleTagSearchChange = useCallback((value: string) => {
    setTagSearch(value);
    eqSearchHook.setTagTerm(value);
  }, [setTagSearch, eqSearchHook]);

  const handleEqSearchChange = useCallback((value: string) => {
    setEqSearch(value);
    eqSearchHook.setEqTerm(value);
  }, [setEqSearch, eqSearchHook]);

  const handleLocalSearchChange = useCallback((value: string) => {
    setLocalSearch(value);
    eqSearchHook.setLocalTerm(value);
  }, [setLocalSearch, eqSearchHook]);

  const handleSelectEquipamento = useCallback((eq: EquipamentoView) => {
    setField('tag', eq.tag || '');
    setField('equipamento', eq.equipamento || '');
    setField('local', eq.local || '');
    setTagSearch(eq.tag || '');
    setEqSearch(eq.equipamento || '');
    setLocalSearch(eq.local || '');
    eqSearchHook.setShowTagSuggestions(false);
    eqSearchHook.setShowEqSuggestions(false);
  }, [setField, setTagSearch, setEqSearch, setLocalSearch, eqSearchHook]);

  const handleSelectLocal = useCallback((loc: string) => {
    setField('local', loc);
    setLocalSearch(loc);
    eqSearchHook.setShowLocalSuggestions(false);
  }, [setField, setLocalSearch, eqSearchHook]);

  const handleImprove = useCallback(async () => {
    const result = await improve(form.descricao);
    if (result) setField('descricao', result);
  }, [form.descricao, improve, setField]);

  // ─── Submit ──────────────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const error = validateOcorrenciaForm(form);
    if (error) { toast.error(error.message); return; }

    setSaving(true);
    const payload = buildPayload(form, isEdit ? undefined : user?.id);

    try {
      if (isEdit) {
        const { error: dbErr } = await supabase.from('ocorrencias').update(payload).eq('id', id!);
        if (dbErr) throw dbErr;
        toast.success('Ocorrência atualizada!');
      } else {
        const { error: dbErr } = await supabase.from('ocorrencias').insert(payload);
        if (dbErr) throw dbErr;
        toast.success('Ocorrência criada!');
      }
      invalidateOcorrencias();
      navigate('/ocorrencias');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  // ─── Render ──────────────────────────────────────────────────────────────
  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex items-center gap-3">
        <Button variant="ghost" onClick={() => navigate('/ocorrencias')} className="touch-target">
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-2xl font-bold">{isEdit ? 'Editar Ocorrência' : 'Nova Ocorrência'}</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <InformacoesGerais
          form={form}
          setField={setField}
          colaboradores={colaboradores}
          isAdmin={!!isAdmin}
          profileArea={profile?.area}
        />

        <EquipamentoSection
          form={form}
          setField={setField}
          tagSearch={tagSearch}
          onTagSearchChange={handleTagSearchChange}
          tagSuggestions={eqSearchHook.tagSuggestions}
          showTagSuggestions={eqSearchHook.showTagSuggestions}
          setShowTagSuggestions={eqSearchHook.setShowTagSuggestions}
          eqSearch={eqSearch}
          onEqSearchChange={handleEqSearchChange}
          eqSuggestions={eqSearchHook.eqSuggestions}
          showEqSuggestions={eqSearchHook.showEqSuggestions}
          setShowEqSuggestions={eqSearchHook.setShowEqSuggestions}
          localSearch={localSearch}
          onLocalSearchChange={handleLocalSearchChange}
          localSuggestions={eqSearchHook.localSuggestions}
          showLocalSuggestions={eqSearchHook.showLocalSuggestions}
          setShowLocalSuggestions={eqSearchHook.setShowLocalSuggestions}
          onSelectEquipamento={handleSelectEquipamento}
          onSelectLocal={handleSelectLocal}
        />

        <DescricaoSection
          descricao={form.descricao}
          onDescricaoChange={v => setField('descricao', v)}
          onImprove={handleImprove}
          improving={improving}
        />

        <ParadaSection
          form={form}
          setField={setField}
          profileArea={profile?.area}
          isAdmin={!!isAdmin}
        />

        <FormActions loading={saving} onCancel={() => navigate('/ocorrencias')} />
      </form>
    </div>
  );
};

export default OcorrenciaForm;

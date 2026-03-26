import { useEffect, useState, useMemo, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { isLeaderOrAbove } from '@/lib/roles';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { ArrowLeft, Save } from 'lucide-react';
import type { Tables } from '@/integrations/supabase/types';
import { useEquipamentoSearch } from '@/hooks/useEquipamentoSearch';

type EquipamentoView = Tables<'vw_equipamentos_app'>;

interface MotorFormState {
  tag: string;
  motor: string;
  identificacao_motor: string;
  carcaca: string;
  fabricante: string;
  potencia: string;
  rpm: string;
  tensao: string;
  corrente: string;
  numero_nf: string;
  data_saida: string;
  destino: string;
  motivo: string;
  status_retorno: string;
  data_retorno: string;
  area: string;
}

const MotorEletricoForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, profile } = useAuth();
  const canChangeArea = isLeaderOrAbove(profile);
  const isEdit = !!id;

  const [loading, setLoading] = useState(false);

  const eqSearch = useEquipamentoSearch();

  const [form, setForm] = useState<MotorFormState>({
    tag: '',
    motor: '',
    identificacao_motor: '',
    carcaca: '',
    fabricante: '',
    potencia: '',
    rpm: '',
    tensao: '',
    corrente: '',
    numero_nf: '',
    data_saida: '',
    destino: '',
    motivo: '',
    status_retorno: 'Pendente',
    data_retorno: '',
    area: profile?.area || 'Elétrica',
  });

  useEffect(() => {
    if (profile?.area && !isEdit) {
      setForm(prev => ({ ...prev, area: profile.area! }));
    }
  }, [profile, isEdit]);

  useEffect(() => {
    if (!isEdit || !id) return;
    let cancelled = false;

    const loadRecord = async () => {
      const { data } = await supabase.from('motores_eletricos').select('*').eq('id', id).single();
      if (cancelled || !data) return;

      setForm({
        tag: data.tag,
        motor: data.motor,
        identificacao_motor: (data.identificacao_motor || '').replace(/^MO/i, ''),
        carcaca: data.carcaca || '',
        fabricante: data.fabricante || '',
        potencia: data.potencia || '',
        rpm: data.rpm || '',
        tensao: data.tensao || '',
        corrente: data.corrente || '',
        numero_nf: data.numero_nf || '',
        data_saida: data.data_saida || '',
        destino: data.destino || '',
        motivo: data.motivo || '',
        status_retorno: data.status_retorno,
        data_retorno: data.data_retorno || '',
        area: data.area,
      });
      eqSearch.setTagTerm(data.tag || '');
    };

    loadRecord();
    return () => { cancelled = true; };
  }, [id, isEdit]);

  const selectEquipamento = (eq: EquipamentoView) => {
    setForm(prev => ({
      ...prev,
      tag: eq.tag || '',
      motor: eq.equipamento || '',
      area: canChangeArea ? (eq.area || prev.area) : prev.area,
    }));
    eqSearch.setTagTerm(eq.tag || '');
    eqSearch.setShowTagSuggestions(false);
  };

  const setFormField = <K extends keyof MotorFormState>(key: K, value: MotorFormState[K]) => {
    setForm(f => ({ ...f, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.tag.trim() || !form.motor.trim()) {
      toast.error('Equipamento é obrigatório');
      return;
    }
    setLoading(true);

    const trimOrNull = (v: string) => v.trim() || null;

    const payload = {
      tag: form.tag.trim(),
      motor: form.motor.trim(),
      identificacao_motor: form.identificacao_motor.trim() ? `MO${form.identificacao_motor.trim()}` : null,
      carcaca: trimOrNull(form.carcaca),
      fabricante: trimOrNull(form.fabricante),
      potencia: trimOrNull(form.potencia),
      rpm: trimOrNull(form.rpm),
      tensao: trimOrNull(form.tensao),
      corrente: trimOrNull(form.corrente),
      numero_nf: trimOrNull(form.numero_nf),
      data_saida: form.data_saida || null,
      destino: trimOrNull(form.destino),
      motivo: trimOrNull(form.motivo),
      status_retorno: form.status_retorno,
      data_retorno: form.data_retorno || null,
      area: form.area,
    };

    try {
      if (isEdit) {
        const { error } = await supabase.from('motores_eletricos').update(payload).eq('id', id!);
        if (error) throw error;
        toast.success('Registro atualizado!');
      } else {
        const { error } = await supabase.from('motores_eletricos').insert({ ...payload, created_by: user?.id });
        if (error) throw error;
        toast.success('Serviço externo registrado!');
      }
      navigate('/motores-eletricos');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Erro ao salvar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={() => navigate('/motores-eletricos')} className="touch-target">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-2xl font-bold">{isEdit ? 'Editar Registro' : 'Registrar Serviço Externo'}</h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-base">Equipamento</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="relative sm:col-span-2">
                <Label>Equipamento (Tag) *</Label>
                <Input
                  value={eqSearch.tagTerm || form.tag}
                  onChange={e => {
                    eqSearch.setTagTerm(e.target.value);
                    setFormField('tag', e.target.value);
                    eqSearch.setShowTagSuggestions(true);
                  }}
                  onFocus={() => eqSearch.setShowTagSuggestions(true)}
                  onBlur={() => setTimeout(() => eqSearch.setShowTagSuggestions(false), 200)}
                  placeholder="Buscar por tag ou nome do equipamento..."
                  className="touch-target mt-1"
                />
                {eqSearch.showTagSuggestions && eqSearch.tagSuggestions.length > 0 && (
                  <div className="absolute z-50 w-full mt-1 bg-card border rounded-md shadow-lg max-h-48 overflow-auto">
                    {eqSearch.tagSuggestions.map((eq) => (
                      <button
                        key={eq.tag}
                        type="button"
                        className="w-full text-left px-3 py-2 hover:bg-muted text-sm"
                        onMouseDown={() => selectEquipamento(eq)}
                      >
                        <span className="font-medium">{eq.tag}</span>
                        <span className="text-muted-foreground"> — {eq.equipamento}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {form.motor && (
                <div className="sm:col-span-2 rounded-md bg-muted/50 px-3 py-2 text-sm">
                  <span className="font-medium text-muted-foreground">Equipamento selecionado:</span>{' '}
                  {form.motor}
                </div>
              )}

              <div>
                <Label>Identificação do Motor</Label>
                <div className="flex mt-1">
                  <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-input bg-muted text-muted-foreground text-sm font-medium">MO</span>
                  <Input
                    value={form.identificacao_motor}
                    onChange={e => setFormField('identificacao_motor', e.target.value.replace(/\D/g, ''))}
                    placeholder="0000201"
                    className="touch-target rounded-l-none"
                  />
                </div>
              </div>
              <div>
                <Label>Potência</Label>
                <Input value={form.potencia} onChange={e => setFormField('potencia', e.target.value)} placeholder="Ex: 75 CV" className="touch-target mt-1" />
              </div>
              <div>
                <Label>Carcaça</Label>
                <Input value={form.carcaca} onChange={e => setFormField('carcaca', e.target.value)} placeholder="Ex: 254T" className="touch-target mt-1" />
              </div>
              <div>
                <Label>Fabricante</Label>
                <Input value={form.fabricante} onChange={e => setFormField('fabricante', e.target.value)} placeholder="Ex: WEG" className="touch-target mt-1" />
              </div>
              <div>
                <Label>RPM</Label>
                <Input value={form.rpm} onChange={e => setFormField('rpm', e.target.value)} placeholder="Ex: 1750" className="touch-target mt-1" />
              </div>
              <div>
                <Label>Tensão</Label>
                <Input value={form.tensao} onChange={e => setFormField('tensao', e.target.value)} placeholder="Ex: 380" className="touch-target mt-1" />
              </div>
              <div>
                <Label>Corrente</Label>
                <Input value={form.corrente} onChange={e => setFormField('corrente', e.target.value)} placeholder="Ex: 10,0A" className="touch-target mt-1" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">Serviço</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label>Motivo / Serviço</Label>
                <Select value={form.motivo || ''} onValueChange={v => setFormField('motivo', v)}>
                  <SelectTrigger className="touch-target mt-1"><SelectValue placeholder="Selecione o serviço" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Rebobinar">Rebobinar</SelectItem>
                    <SelectItem value="Reparo geral">Reparo geral</SelectItem>
                    <SelectItem value="Outro">Outro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Destino</Label>
                <Input value={form.destino} onChange={e => setFormField('destino', e.target.value)} placeholder="Para onde foi enviado" className="touch-target mt-1" />
              </div>
              <div>
                <Label>Nº Nota Fiscal</Label>
                <Input value={form.numero_nf} onChange={e => setFormField('numero_nf', e.target.value)} placeholder="Número da NF" className="touch-target mt-1" />
              </div>
              <div>
                <Label>Data de Saída</Label>
                <Input type="date" value={form.data_saida} onChange={e => setFormField('data_saida', e.target.value)} className="touch-target mt-1" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">Retorno</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label>Status de Retorno</Label>
                <Select value={form.status_retorno} onValueChange={v => setFormField('status_retorno', v)}>
                  <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Pendente">Pendente</SelectItem>
                    <SelectItem value="Retornado">Retornado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Data de Retorno</Label>
                <Input type="date" value={form.data_retorno} onChange={e => setFormField('data_retorno', e.target.value)} className="touch-target mt-1" />
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-3">
            <Button type="button" variant="outline" onClick={() => navigate('/motores-eletricos')} className="flex-1">
              Cancelar
            </Button>
            <Button type="submit" disabled={loading} className="flex-1">
              <Save className="mr-2 h-4 w-4" />
              {loading ? 'Salvando...' : isEdit ? 'Salvar alterações' : 'Registrar'}
            </Button>
          </div>
        </form>
    </div>
  );
};

export default MotorEletricoForm;

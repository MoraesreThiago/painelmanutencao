import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { ArrowLeft, Save, Wand2, Loader2 } from 'lucide-react';
import type { Equipamento, Colaborador } from '@/types/database';
import { fetchAllEquipamentos } from '@/lib/fetchAllEquipamentos';

const OcorrenciaForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, profile } = useAuth();
  const isAdmin = profile?.perfil === 'administrador';
  const isEdit = !!id;

  const [loading, setLoading] = useState(false);
  const [improving, setImproving] = useState(false);
  const [equipamentos, setEquipamentos] = useState<Equipamento[]>([]);
  const [colaboradores, setColaboradores] = useState<Colaborador[]>([]);
  const [tagSearch, setTagSearch] = useState('');
  const [eqSearch, setEqSearch] = useState('');
  const [showTagSuggestions, setShowTagSuggestions] = useState(false);
  const [showEqSuggestions, setShowEqSuggestions] = useState(false);
  const [localSearch, setLocalSearch] = useState('');
  const [showLocalSuggestions, setShowLocalSuggestions] = useState(false);

  const getHorarioByTime = () => {
    const now = new Date();
    const h = now.getHours();
    const m = now.getMinutes();
    const totalMin = h * 60 + m;
    return (totalMin >= 430 && totalMin < 1150) ? 'Dia' : 'Amanhecida';
  };

  const getTurnoByDate = () => {
    const now = new Date();
    const horario = getHorarioByTime();
    // Reference: 2026-03-17 is cycle day 0
    const ref = new Date(2025, 2, 17); // March 17, 2025 = cycle day 0 (D dia / C amanhecida)
    const diffDays = Math.floor((now.getTime() - ref.getTime()) / 86400000);
    const cycleDay = ((diffDays % 8) + 8) % 8;
    const diaShifts =       ['D', 'D', 'B', 'B', 'C', 'C', 'A', 'A'];
    const amanhecidaShifts = ['C', 'C', 'A', 'A', 'D', 'D', 'B', 'B'];
    return horario === 'Dia' ? diaShifts[cycleDay] : amanhecidaShifts[cycleDay];
  };

  const [form, setForm] = useState({
    data_ocorrencia: new Date().toISOString().split('T')[0],
    horario: getHorarioByTime(),
    turno: getTurnoByDate(),
    colaborador_id: '',
    tag: '',
    equipamento: '',
    local: '',
    area: profile?.area || 'Elétrica',
    tipo_ocorrencia: '',
    descricao: '',
    status: 'Pendente',
    houve_parada: false,
    tipo_parada: '',
    tempo_parada: '',
    gerar_os: false,
    prioridade_os: '',
    observacao_os: '',
    tipo_manutencao_os: '',
  });

  useEffect(() => {
    const loadData = async () => {
      const [eqs, { data: cols }] = await Promise.all([
        fetchAllEquipamentos(),
        (supabase as any).from('colaboradores').select('*').eq('status', 'Ativo').order('nome'),
      ]);
      setEquipamentos(eqs);
      setColaboradores((cols || []) as Colaborador[]);

      if (isEdit) {
        const { data } = await (supabase as any).from('ocorrencias').select('*').eq('id', id).single();
        if (data) {
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
            status: data.status,
            houve_parada: data.houve_parada || false,
            tipo_parada: data.tipo_parada || '',
            tempo_parada: data.tempo_parada || '',
            gerar_os: data.gerar_os || false,
            prioridade_os: data.prioridade_os || '',
            observacao_os: data.observacao_os || '',
            tipo_manutencao_os: data.tipo_manutencao_os || '',
          });
          setTagSearch(data.tag || '');
          setEqSearch(data.equipamento || '');
          setLocalSearch(data.local || '');
        }
      }
    };
    loadData();
  }, [id, isEdit]);

  const selectEquipamento = (eq: Equipamento) => {
    setForm(f => ({ ...f, tag: eq.tag || '', equipamento: eq.equipamento, local: eq.local || '', area: eq.area || f.area }));
    setTagSearch(eq.tag || '');
    setEqSearch(eq.equipamento);
    setLocalSearch(eq.local || '');
    setShowTagSuggestions(false);
    setShowEqSuggestions(false);
  };

  const tagSuggestions = equipamentos.filter(e => e.tag?.toLowerCase().includes(tagSearch.toLowerCase()) && tagSearch.length > 0);
  const eqSuggestions = equipamentos.filter(e => e.equipamento.toLowerCase().includes(eqSearch.toLowerCase()) && eqSearch.length > 0);
  const localSuggestions = [...new Set(equipamentos.map(e => e.local).filter((l): l is string => !!l && l.toLowerCase().includes(localSearch.toLowerCase()) && localSearch.length > 0))];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.descricao.trim()) { toast.error('Descrição é obrigatória'); return; }
    setLoading(true);

    const payload: any = {
      ...form,
      colaborador_id: form.colaborador_id || null,
      tipo_parada: form.houve_parada ? form.tipo_parada : null,
      tempo_parada: form.houve_parada && form.tempo_parada ? `${form.tempo_parada} minutes` : null,
      prioridade_os: form.gerar_os ? form.prioridade_os : null,
      observacao_os: form.gerar_os ? form.observacao_os : null,
      tipo_manutencao_os: form.gerar_os ? form.tipo_manutencao_os : null,
    };

    try {
      if (isEdit) {
        const { error } = await (supabase as any).from('ocorrencias').update(payload).eq('id', id);
        if (error) throw error;
        toast.success('Ocorrência atualizada!');
      } else {
        payload.created_by = user?.id;
        const { error } = await (supabase as any).from('ocorrencias').insert(payload);
        if (error) throw error;
        toast.success('Ocorrência criada!');
      }
      navigate('/ocorrencias');
    } catch (err: any) {
      toast.error(err.message || 'Erro ao salvar');
    } finally {
      setLoading(false);
    }
  };

  const set = (key: string, value: any) => setForm(f => ({ ...f, [key]: value }));

  const handleImproveDescription = async () => {
    if (!form.descricao.trim()) { toast.error('Digite uma descrição primeiro'); return; }
    setImproving(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/improve-description`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ descricao: form.descricao }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Erro ao melhorar descrição');
      if (data.improved) {
        set('descricao', data.improved);
        toast.success('Descrição aprimorada pela IA!');
      }
    } catch (err: any) {
      toast.error(err.message || 'Erro ao processar com IA');
    } finally {
      setImproving(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={() => navigate('/ocorrencias')} className="touch-target">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-2xl font-bold">{isEdit ? 'Editar Ocorrência' : 'Nova Ocorrência'}</h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-base">Informações Gerais</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label>Data da Ocorrência *</Label>
                <Input type="date" value={form.data_ocorrencia} onChange={e => set('data_ocorrencia', e.target.value)} required className="touch-target mt-1" />
              </div>
              <div>
                <Label>Horário *</Label>
                <Select value={form.horario} onValueChange={v => set('horario', v)}>
                  <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Dia">Dia</SelectItem>
                    <SelectItem value="Amanhecida">Amanhecida</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Turno *</Label>
                <Select value={form.turno} onValueChange={v => set('turno', v)}>
                  <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {['A', 'B', 'C', 'D', 'ADM'].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Colaborador</Label>
                <Select value={form.colaborador_id} onValueChange={v => set('colaborador_id', v)}>
                  <SelectTrigger className="touch-target mt-1"><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    {colaboradores.map(c => <SelectItem key={c.id} value={c.id}>{c.nome} ({c.area})</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              {isEdit && (
                <div>
                  <Label>Status</Label>
                  <Select value={form.status} onValueChange={v => set('status', v)}>
                    <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Pendente">Pendente</SelectItem>
                      <SelectItem value="Liberado">Liberado</SelectItem>
                      <SelectItem value="Em andamento">Em andamento</SelectItem>
                      <SelectItem value="Realizada">Realizada</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">Equipamento</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="relative">
                <Label>TAG</Label>
                <Input value={tagSearch} onChange={e => { setTagSearch(e.target.value); set('tag', e.target.value); setShowTagSuggestions(true); }} onFocus={() => setShowTagSuggestions(true)} onBlur={() => setTimeout(() => setShowTagSuggestions(false), 200)} placeholder="Digite a TAG" className="touch-target mt-1" />
                {showTagSuggestions && tagSuggestions.length > 0 && (
                  <div className="absolute z-50 w-full mt-1 bg-card border rounded-md shadow-lg max-h-48 overflow-auto">
                    {tagSuggestions.map(eq => (
                      <button key={eq.id} type="button" className="w-full text-left px-3 py-2 hover:bg-muted text-sm" onMouseDown={() => selectEquipamento(eq)}>
                        <span className="font-medium">{eq.tag}</span> — {eq.equipamento}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div className="relative">
                <Label>Equipamento</Label>
                <Input value={eqSearch} onChange={e => { setEqSearch(e.target.value); set('equipamento', e.target.value); setShowEqSuggestions(true); }} onFocus={() => setShowEqSuggestions(true)} onBlur={() => setTimeout(() => setShowEqSuggestions(false), 200)} placeholder="Digite o equipamento" className="touch-target mt-1" />
                {showEqSuggestions && eqSuggestions.length > 0 && (
                  <div className="absolute z-50 w-full mt-1 bg-card border rounded-md shadow-lg max-h-48 overflow-auto">
                    {eqSuggestions.map(eq => (
                      <button key={eq.id} type="button" className="w-full text-left px-3 py-2 hover:bg-muted text-sm" onMouseDown={() => selectEquipamento(eq)}>
                        <span className="font-medium">{eq.equipamento}</span>{eq.tag ? ` — ${eq.tag}` : ''}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div className="relative">
                <Label>Local</Label>
                <Input value={localSearch || form.local} onChange={e => { setLocalSearch(e.target.value); set('local', e.target.value); setShowLocalSuggestions(true); }} onFocus={() => setShowLocalSuggestions(true)} onBlur={() => setTimeout(() => setShowLocalSuggestions(false), 200)} placeholder="Digite o local" className="touch-target mt-1" />
                {showLocalSuggestions && localSearch.length > 0 && localSuggestions.length > 0 && (
                  <div className="absolute z-50 w-full mt-1 bg-card border rounded-md shadow-lg max-h-48 overflow-auto">
                    {localSuggestions.map((loc, i) => (
                      <button key={i} type="button" className="w-full text-left px-3 py-2 hover:bg-muted text-sm" onMouseDown={() => { set('local', loc); setLocalSearch(loc); setShowLocalSuggestions(false); }}>
                        {loc}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div>
                <Label>Tipo de Ocorrência</Label>
                <Select value={form.tipo_ocorrencia} onValueChange={v => set('tipo_ocorrencia', v)}>
                  <SelectTrigger className="touch-target mt-1"><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Corretiva">Corretiva</SelectItem>
                    <SelectItem value="Preventiva">Preventiva</SelectItem>
                    <SelectItem value="Preditiva">Preditiva</SelectItem>
                    <SelectItem value="Inspeção">Inspeção</SelectItem>
                    <SelectItem value="Melhoria">Melhoria</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Descrição</CardTitle>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleImproveDescription}
                  disabled={improving || !form.descricao.trim()}
                  className="gap-1.5"
                >
                  {improving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
                  {improving ? 'Melhorando...' : 'Melhorar com IA'}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Textarea value={form.descricao} onChange={e => set('descricao', e.target.value)} placeholder="Descreva a ocorrência..." rows={4} required className="touch-target" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">Parada</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Switch checked={form.houve_parada} onCheckedChange={v => set('houve_parada', v)} />
                <Label>Houve parada?</Label>
              </div>
              {form.houve_parada && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <Label>Tipo de Parada</Label>
                    <Select value={form.tipo_parada} onValueChange={v => set('tipo_parada', v)}>
                      <SelectTrigger className="touch-target mt-1"><SelectValue placeholder="Selecione" /></SelectTrigger>
                      <SelectContent>
                        {profile?.area === 'Elétrica' && <SelectItem value="Elétrica">Elétrica</SelectItem>}
                        {profile?.area === 'Elétrica' && <SelectItem value="Instrumentação">Instrumentação</SelectItem>}
                        {profile?.area === 'Mecânica' && <SelectItem value="Mecânica">Mecânica</SelectItem>}
                        {profile?.area === 'Mecânica' && <SelectItem value="Instrumentação">Instrumentação</SelectItem>}
                        {profile?.perfil === 'administrador' && (
                          <>
                            <SelectItem value="Elétrica">Elétrica</SelectItem>
                            <SelectItem value="Instrumentação">Instrumentação</SelectItem>
                            <SelectItem value="Mecânica">Mecânica</SelectItem>
                          </>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Tempo de Parada (minutos)</Label>
                    <Input type="number" value={form.tempo_parada} onChange={e => set('tempo_parada', e.target.value)} placeholder="Ex: 30" className="touch-target mt-1" />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>


          <div className="flex gap-3 pb-6">
            <Button type="button" variant="outline" onClick={() => navigate('/ocorrencias')} className="touch-target flex-1">Cancelar</Button>
            <Button type="submit" disabled={loading} className="touch-target flex-1">
              <Save className="h-5 w-5 mr-2" /> {loading ? 'Salvando...' : 'Salvar'}
            </Button>
          </div>
        </form>
      </div>
    </Layout>
  );
};

export default OcorrenciaForm;

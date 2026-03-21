import { useEffect, useState, useMemo } from 'react';
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
import { format } from 'date-fns';

interface Equipamento {
  tag: string | null;
  equipamento: string | null;
  area: string | null;
  local: string | null;
}

const MotorEletricoForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, profile } = useAuth();
  const isAdmin = profile?.perfil === 'administrador';
  const canChangeArea = isLeaderOrAbove(profile);
  const isEdit = !!id;

  const [loading, setLoading] = useState(false);
  const [equipamentos, setEquipamentos] = useState<Equipamento[]>([]);
  const [tagSearch, setTagSearch] = useState('');
  const [showTagSuggestions, setShowTagSuggestions] = useState(false);

  const [form, setForm] = useState({
    tag: '',
    motor: '',
    identificacao_motor: '',
    carcaca: '',
    fabricante: '',
    potencia: '',
    numero_nf: '',
    data_saida: format(new Date(), 'yyyy-MM-dd'),
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
    const loadData = async () => {
      const { data: eqs } = await (supabase as any)
        .from('vw_equipamentos_app')
        .select('tag, equipamento, area, local')
        .order('tag');
      setEquipamentos((eqs || []) as Equipamento[]);

      if (isEdit) {
        const { data } = await (supabase as any).from('motores_eletricos').select('*').eq('id', id).single();
        if (data) {
          setForm({
            tag: data.tag,
            motor: data.motor,
            identificacao_motor: (data.identificacao_motor || '').replace(/^MO/i, ''),
            carcaca: data.carcaca || '',
            fabricante: data.fabricante || '',
            potencia: data.potencia || '',
            numero_nf: data.numero_nf || '',
            data_saida: data.data_saida,
            destino: data.destino || '',
            motivo: data.motivo || '',
            status_retorno: data.status_retorno,
            data_retorno: data.data_retorno || '',
            area: data.area,
          });
          setTagSearch(data.tag || '');
        }
      }
    };
    loadData();
  }, [id, isEdit]);

  const tagSuggestions = useMemo(() => {
    if (!tagSearch || tagSearch.length < 1) return [];
    const q = tagSearch.toLowerCase();
    return equipamentos.filter(e =>
      (e.tag?.toLowerCase().includes(q)) ||
      (e.equipamento?.toLowerCase().includes(q))
    ).slice(0, 30);
  }, [equipamentos, tagSearch]);

  const selectEquipamento = (eq: Equipamento) => {
    setForm(prev => ({
      ...prev,
      tag: eq.tag || '',
      motor: eq.equipamento || '',
      area: canChangeArea ? (eq.area_manutencao || eq.area_fabrica || prev.area) : prev.area,
    }));
    setTagSearch(eq.tag || '');
    setShowTagSuggestions(false);
  };

  const set = (key: string, value: any) => setForm(f => ({ ...f, [key]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.tag.trim() || !form.motor.trim() || !form.data_saida) {
      toast.error('Equipamento e Data de Saída são obrigatórios');
      return;
    }
    setLoading(true);

    const payload: any = {
      tag: (form.tag || '').trim(),
      motor: (form.motor || '').trim(),
      identificacao_motor: (form.identificacao_motor || '').trim() ? `MO${(form.identificacao_motor || '').trim()}` : null,
      carcaca: (form.carcaca || '').trim() || null,
      fabricante: (form.fabricante || '').trim() || null,
      potencia: (form.potencia || '').trim() || null,
      numero_nf: (form.numero_nf || '').trim() || null,
      data_saida: form.data_saida,
      destino: (form.destino || '').trim() || null,
      motivo: (form.motivo || '').trim() || null,
      status_retorno: form.status_retorno,
      data_retorno: form.data_retorno || null,
      area: form.area,
    };

    try {
      if (isEdit) {
        const { error } = await (supabase as any).from('motores_eletricos').update(payload).eq('id', id);
        if (error) throw error;
        toast.success('Registro atualizado!');
      } else {
        payload.created_by = user?.id;
        const { error } = await (supabase as any).from('motores_eletricos').insert(payload);
        if (error) throw error;
        toast.success('Serviço externo registrado!');
      }
      navigate('/motores-eletricos');
    } catch (err: any) {
      toast.error(err.message || 'Erro ao salvar');
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
                  value={tagSearch || form.tag}
                  onChange={e => {
                    setTagSearch(e.target.value);
                    set('tag', e.target.value);
                    setShowTagSuggestions(true);
                  }}
                  onFocus={() => setShowTagSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowTagSuggestions(false), 200)}
                  placeholder="Buscar por tag ou nome do equipamento..."
                  className="touch-target mt-1"
                />
                {showTagSuggestions && tagSuggestions.length > 0 && (
                  <div className="absolute z-50 w-full mt-1 bg-card border rounded-md shadow-lg max-h-48 overflow-auto">
                    {tagSuggestions.map((eq) => (
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
                    onChange={e => set('identificacao_motor', e.target.value.replace(/\D/g, ''))}
                    placeholder="0000201"
                    className="touch-target rounded-l-none"
                  />
                </div>
              </div>
              <div>
                <Label>Potência</Label>
                <Input value={form.potencia} onChange={e => set('potencia', e.target.value)} placeholder="Ex: 75 CV" className="touch-target mt-1" />
              </div>
              <div>
                <Label>Carcaça</Label>
                <Input value={form.carcaca} onChange={e => set('carcaca', e.target.value)} placeholder="Ex: 254T" className="touch-target mt-1" />
              </div>
              <div>
                <Label>Fabricante</Label>
                <Input value={form.fabricante} onChange={e => set('fabricante', e.target.value)} placeholder="Ex: WEG" className="touch-target mt-1" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">Serviço</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label>Motivo / Serviço</Label>
                <Select value={form.motivo || ''} onValueChange={v => set('motivo', v)}>
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
                <Input value={form.destino} onChange={e => set('destino', e.target.value)} placeholder="Para onde foi enviado" className="touch-target mt-1" />
              </div>
              <div>
                <Label>Nº Nota Fiscal</Label>
                <Input value={form.numero_nf} onChange={e => set('numero_nf', e.target.value)} placeholder="Número da NF" className="touch-target mt-1" />
              </div>
              <div>
                <Label>Data de Saída *</Label>
                <Input type="date" value={form.data_saida} onChange={e => set('data_saida', e.target.value)} className="touch-target mt-1" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">Retorno</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label>Status de Retorno</Label>
                <Select value={form.status_retorno} onValueChange={v => set('status_retorno', v)}>
                  <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Pendente">Pendente</SelectItem>
                    <SelectItem value="Retornado">Retornado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Data de Retorno</Label>
                <Input type="date" value={form.data_retorno} onChange={e => set('data_retorno', e.target.value)} className="touch-target mt-1" />
              </div>

              {canChangeArea && (
                <div>
                  <Label>Área</Label>
                  <Select value={form.area} onValueChange={v => set('area', v)}>
                    <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Elétrica">Elétrica</SelectItem>
                      <SelectItem value="Mecânica">Mecânica</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
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

import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, Search, RotateCcw } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { format } from 'date-fns';

interface MotorEletrico {
  id: string;
  tag: string;
  motor: string;
  potencia: string | null;
  numero_nf: string;
  data_saida: string;
  destino: string | null;
  motivo: string | null;
  status_retorno: string;
  data_retorno: string | null;
  area: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

const emptyForm = {
  tag: '', motor: '', potencia: '', numero_nf: '', data_saida: '',
  destino: '', motivo: '', status_retorno: 'Pendente', data_retorno: '', area: 'Elétrica',
};

const MotoresEletricos = () => {
  const { profile } = useAuth();
  const isAdmin = profile?.perfil === 'administrador';
  const userArea = profile?.area || 'Elétrica';

  const [items, setItems] = useState<MotorEletrico[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<MotorEletrico | null>(null);
  const [form, setForm] = useState({ ...emptyForm, area: userArea });

  const load = async () => {
    setLoading(true);
    const { data } = await (supabase as any)
      .from('motores_eletricos')
      .select('*')
      .order('data_saida', { ascending: false });
    setItems((data || []) as MotorEletrico[]);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const openNew = () => {
    setEditing(null);
    setForm({ ...emptyForm, area: userArea });
    setDialogOpen(true);
  };

  const openEdit = (m: MotorEletrico) => {
    setEditing(m);
    setForm({
      tag: m.tag, motor: m.motor, potencia: m.potencia || '',
      numero_nf: m.numero_nf, data_saida: m.data_saida,
      destino: m.destino || '', motivo: m.motivo || '',
      status_retorno: m.status_retorno, data_retorno: m.data_retorno || '',
      area: m.area,
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!form.tag.trim() || !form.motor.trim() || !form.numero_nf.trim() || !form.data_saida) {
      toast.error('Tag, Motor, Nota Fiscal e Data de Saída são obrigatórios');
      return;
    }
    const payload: any = {
      tag: form.tag.trim(),
      motor: form.motor.trim(),
      potencia: form.potencia.trim() || null,
      numero_nf: form.numero_nf.trim(),
      data_saida: form.data_saida,
      destino: form.destino.trim() || null,
      motivo: form.motivo.trim() || null,
      status_retorno: form.status_retorno,
      data_retorno: form.data_retorno || null,
      area: form.area,
    };
    try {
      if (editing) {
        await (supabase as any).from('motores_eletricos').update(payload).eq('id', editing.id);
        toast.success('Motor atualizado!');
      } else {
        await (supabase as any).from('motores_eletricos').insert(payload);
        toast.success('Motor cadastrado!');
      }
      setDialogOpen(false);
      load();
    } catch (err: any) { toast.error(err.message); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Deseja excluir este motor?')) return;
    await (supabase as any).from('motores_eletricos').delete().eq('id', id);
    toast.success('Motor excluído!');
    load();
  };

  const handleMarcarRetorno = async (m: MotorEletrico) => {
    const today = format(new Date(), 'yyyy-MM-dd');
    await (supabase as any).from('motores_eletricos')
      .update({ status_retorno: 'Retornado', data_retorno: today })
      .eq('id', m.id);
    toast.success('Motor marcado como retornado!');
    load();
  };

  const filtered = items.filter(m =>
    m.tag.toLowerCase().includes(search.toLowerCase()) ||
    m.motor.toLowerCase().includes(search.toLowerCase()) ||
    m.numero_nf.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Motores Elétricos</h1>
            <p className="text-sm text-muted-foreground mt-1">Controle de saída e retorno de motores</p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button onClick={openNew}><Plus className="mr-2 h-4 w-4" />Novo Motor</Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editing ? 'Editar Motor' : 'Cadastrar Motor'}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-2">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Tag *</Label>
                    <Input value={form.tag} onChange={e => setForm({ ...form, tag: e.target.value })} placeholder="Ex: MT-001" />
                  </div>
                  <div className="space-y-2">
                    <Label>Potência</Label>
                    <Input value={form.potencia} onChange={e => setForm({ ...form, potencia: e.target.value })} placeholder="Ex: 75 CV" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Motor *</Label>
                  <Input value={form.motor} onChange={e => setForm({ ...form, motor: e.target.value })} placeholder="Descrição do motor" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Nº Nota Fiscal *</Label>
                    <Input value={form.numero_nf} onChange={e => setForm({ ...form, numero_nf: e.target.value })} placeholder="Número da NF" />
                  </div>
                  <div className="space-y-2">
                    <Label>Data de Saída *</Label>
                    <Input type="date" value={form.data_saida} onChange={e => setForm({ ...form, data_saida: e.target.value })} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Destino</Label>
                  <Input value={form.destino} onChange={e => setForm({ ...form, destino: e.target.value })} placeholder="Para onde foi enviado" />
                </div>
                <div className="space-y-2">
                  <Label>Motivo</Label>
                  <Select value={form.motivo || ''} onValueChange={v => setForm({ ...form, motivo: v })}>
                    <SelectTrigger><SelectValue placeholder="Selecione o motivo" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Rebobinar">Rebobinar</SelectItem>
                      <SelectItem value="Troca de rolamento">Troca de rolamento</SelectItem>
                      <SelectItem value="Reparo geral">Reparo geral</SelectItem>
                      <SelectItem value="Troca">Troca</SelectItem>
                      <SelectItem value="Outro">Outro</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Status de Retorno</Label>
                    <Select value={form.status_retorno} onValueChange={v => setForm({ ...form, status_retorno: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Pendente">Pendente</SelectItem>
                        <SelectItem value="Retornado">Retornado</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Data de Retorno</Label>
                    <Input type="date" value={form.data_retorno} onChange={e => setForm({ ...form, data_retorno: e.target.value })} />
                  </div>
                </div>
                {isAdmin && (
                  <div className="space-y-2">
                    <Label>Área</Label>
                    <Select value={form.area} onValueChange={v => setForm({ ...form, area: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Elétrica">Elétrica</SelectItem>
                        <SelectItem value="Mecânica">Mecânica</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}
                <Button className="w-full" onClick={handleSave}>
                  {editing ? 'Salvar alterações' : 'Cadastrar'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar por tag, motor ou NF..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
          </div>
        ) : filtered.length === 0 ? (
          <Card><CardContent className="py-12 text-center text-muted-foreground">Nenhum motor encontrado.</CardContent></Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filtered.map(m => (
              <Card key={m.id} className="relative">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-base">{m.tag}</CardTitle>
                      <p className="text-sm text-muted-foreground mt-0.5">{m.motor}</p>
                    </div>
                    <Badge variant={m.status_retorno === 'Retornado' ? 'default' : 'destructive'}>
                      {m.status_retorno}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  {m.potencia && <p><span className="font-medium text-muted-foreground">Potência:</span> {m.potencia}</p>}
                  <p><span className="font-medium text-muted-foreground">NF:</span> {m.numero_nf}</p>
                  <p><span className="font-medium text-muted-foreground">Saída:</span> {format(new Date(m.data_saida + 'T12:00:00'), 'dd/MM/yyyy')}</p>
                  {m.destino && <p><span className="font-medium text-muted-foreground">Destino:</span> {m.destino}</p>}
                  {m.motivo && <p><span className="font-medium text-muted-foreground">Motivo:</span> {m.motivo}</p>}
                  {m.data_retorno && <p><span className="font-medium text-muted-foreground">Retorno:</span> {format(new Date(m.data_retorno + 'T12:00:00'), 'dd/MM/yyyy')}</p>}

                  <div className="flex gap-2 pt-2 border-t">
                    {m.status_retorno === 'Pendente' && (
                      <Button size="sm" variant="outline" onClick={() => handleMarcarRetorno(m)}>
                        <RotateCcw className="mr-1 h-3.5 w-3.5" />Marcar Retorno
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" onClick={() => openEdit(m)}>
                      <Edit className="h-3.5 w-3.5" />
                    </Button>
                    {isAdmin && (
                      <Button size="sm" variant="ghost" className="text-destructive hover:text-destructive" onClick={() => handleDelete(m.id)}>
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default MotoresEletricos;

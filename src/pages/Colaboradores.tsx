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
import { Plus, Edit, Trash2, Search } from 'lucide-react';
import type { Colaborador } from '@/types/database';

const Colaboradores = () => {
  const [items, setItems] = useState<Colaborador[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Colaborador | null>(null);
  const [form, setForm] = useState({ nome: '', area: 'Elétrica', turno: 'A', cargo: '', status: 'Ativo' });

  const load = async () => {
    setLoading(true);
    const { data } = await (supabase as any).from('colaboradores').select('*').order('nome');
    setItems((data || []) as Colaborador[]);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const openNew = () => { setEditing(null); setForm({ nome: '', area: 'Elétrica', turno: 'A', cargo: '', status: 'Ativo' }); setDialogOpen(true); };
  const openEdit = (c: Colaborador) => { setEditing(c); setForm({ nome: c.nome, area: c.area, turno: c.turno, cargo: c.cargo || '', status: c.status }); setDialogOpen(true); };

  const handleSave = async () => {
    if (!form.nome.trim()) { toast.error('Nome é obrigatório'); return; }
    try {
      if (editing) {
        await (supabase as any).from('colaboradores').update(form).eq('id', editing.id);
        toast.success('Colaborador atualizado!');
      } else {
        await (supabase as any).from('colaboradores').insert(form);
        toast.success('Colaborador cadastrado!');
      }
      setDialogOpen(false);
      load();
    } catch (err: any) { toast.error(err.message); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Excluir colaborador?')) return;
    const { error } = await (supabase as any).from('colaboradores').delete().eq('id', id);
    if (error) { toast.error('Sem permissão para excluir ou erro: ' + error.message); return; }
    toast.success('Colaborador excluído!');
    load();
  };

  const filtered = items.filter(c => !search || c.nome.toLowerCase().includes(search.toLowerCase()));
  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  return (
    <Layout>
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-bold">Colaboradores</h1>
          <Button onClick={openNew} className="touch-target"><Plus className="h-5 w-5 mr-2" /> Novo</Button>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Buscar por nome..." value={search} onChange={e => setSearch(e.target.value)} className="pl-10 touch-target" />
        </div>

        {loading ? (
          <div className="flex justify-center py-8"><div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" /></div>
        ) : (
          <div className="space-y-2">
            {filtered.map(c => (
              <Card key={c.id}>
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="font-semibold">{c.nome}</p>
                    <div className="flex flex-wrap gap-2 mt-1">
                      <Badge variant="secondary">{c.area}</Badge>
                      <Badge variant="outline">Turno {c.turno}</Badge>
                      {c.cargo && <Badge variant="outline">{c.cargo}</Badge>}
                      <Badge className={c.status === 'Ativo' ? 'bg-status-realizada text-primary-foreground' : 'bg-muted text-muted-foreground'}>{c.status}</Badge>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" onClick={() => openEdit(c)} className="touch-target"><Edit className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(c.id)} className="touch-target text-destructive"><Trash2 className="h-4 w-4" /></Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader><DialogTitle>{editing ? 'Editar' : 'Novo'} Colaborador</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Nome *</Label><Input value={form.nome} onChange={e => set('nome', e.target.value)} className="touch-target mt-1" /></div>
              <div><Label>Área *</Label>
                <Select value={form.area} onValueChange={v => set('area', v)}>
                  <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="Elétrica">Elétrica</SelectItem><SelectItem value="Mecânica">Mecânica</SelectItem></SelectContent>
                </Select>
              </div>
              <div><Label>Turno *</Label>
                <Select value={form.turno} onValueChange={v => set('turno', v)}>
                  <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent>{['A','B','C','D','ADM'].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div><Label>Cargo</Label><Input value={form.cargo} onChange={e => set('cargo', e.target.value)} className="touch-target mt-1" /></div>
              <div><Label>Status</Label>
                <Select value={form.status} onValueChange={v => set('status', v)}>
                  <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="Ativo">Ativo</SelectItem><SelectItem value="Inativo">Inativo</SelectItem></SelectContent>
                </Select>
              </div>
              <Button onClick={handleSave} className="w-full touch-target">Salvar</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
};

export default Colaboradores;

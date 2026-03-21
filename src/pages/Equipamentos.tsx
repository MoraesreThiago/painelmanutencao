import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const PAGE_SIZE = 20;

const Equipamentos = () => {
  const { profile } = useAuth();
  const isAdmin = profile?.perfil === 'administrador';
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<any | null>(null);
  const [form, setForm] = useState({ tag: '', equipamento: '', local: '', area: 'Elétrica', status: 'Ativo' });
  const [page, setPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);

  const load = async () => {
    setLoading(true);
    const from = page * PAGE_SIZE;
    const to = from + PAGE_SIZE - 1;

    let countQuery = (supabase as any).from('vw_equipamentos_app').select('*', { count: 'exact', head: true });
    let dataQuery = (supabase as any).from('vw_equipamentos_app').select('*').order('tag', { ascending: true }).range(from, to);

    if (search.trim()) {
      const s = `%${search.trim()}%`;
      const orFilter = `tag.ilike.${s},equipamento.ilike.${s}`;
      countQuery = countQuery.or(orFilter);
      dataQuery = dataQuery.or(orFilter);
    }

    const [{ count }, { data, error }] = await Promise.all([countQuery, dataQuery]);
    if (error) {
      toast.error(error.message || 'Erro ao carregar equipamentos');
    }
    setTotalCount(count || 0);
    setItems(data || []);
    setLoading(false);
  };

  useEffect(() => { setPage(0); }, [search]);
  useEffect(() => { load(); }, [search, page]);

  const openNew = () => { setEditing(null); setForm({ tag: '', equipamento: '', local: '', area: 'Elétrica', status: 'Ativo' }); setDialogOpen(true); };
  const openEdit = (e: any) => { setEditing(e); setForm({ tag: e.tag || '', equipamento: e.equipamento, local: e.local || '', area: e.area || 'Elétrica', status: e.status }); setDialogOpen(true); };

  const handleSave = async () => {
    if (!form.equipamento.trim()) { toast.error('Equipamento é obrigatório'); return; }
    try {
      if (editing) {
        await (supabase as any).from('equipamentos').update(form).eq('id', editing.id);
        toast.success('Equipamento atualizado!');
      } else {
        await (supabase as any).from('equipamentos').insert(form);
        toast.success('Equipamento cadastrado!');
      }
      setDialogOpen(false);
      load();
    } catch (err: any) { toast.error(err.message); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Excluir equipamento?')) return;
    const { error } = await (supabase as any).from('equipamentos').delete().eq('id', id);
    if (error) { toast.error('Sem permissão ou erro: ' + error.message); return; }
    toast.success('Equipamento excluído!');
    load();
  };

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));
  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  return (
    <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-bold">Equipamentos</h1>
          {isAdmin && <Button onClick={openNew} className="touch-target"><Plus className="h-5 w-5 mr-2" /> Novo</Button>}
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Buscar por TAG ou equipamento..." value={search} onChange={e => setSearch(e.target.value)} className="pl-10 touch-target" />
        </div>

        {loading ? (
          <div className="flex justify-center py-8"><div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" /></div>
        ) : items.length === 0 ? (
          <Card><CardContent className="p-8 text-center text-muted-foreground">Nenhum equipamento encontrado.</CardContent></Card>
        ) : (
          <>
            <div className="space-y-2">
              {items.map((e, i) => (
                <Card key={e.tag + '-' + i}>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">{e.equipamento}</span>
                        {e.tag && <Badge variant="outline">{e.tag}</Badge>}
                      </div>
                      <div className="flex flex-wrap gap-2 mt-1 text-sm text-muted-foreground">
                        {e.local && <span>{e.local}</span>}
                        {e.area && <Badge variant="secondary">{e.area}</Badge>}
                        <Badge className={e.status === 'Ativo' ? 'bg-status-realizada text-primary-foreground' : 'bg-muted text-muted-foreground'}>{e.status}</Badge>
                      </div>
                    </div>
                    {isAdmin && (
                      <div className="flex gap-1">
                        <Button variant="ghost" size="sm" onClick={() => openEdit(e)} className="touch-target"><Edit className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(e.id)} className="touch-target text-destructive"><Trash2 className="h-4 w-4" /></Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between pt-2">
              <p className="text-sm text-muted-foreground">
                {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, totalCount)} de {totalCount}
              </p>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(p => p - 1)} className="touch-target">
                  <ChevronLeft className="h-4 w-4 mr-1" /> Anterior
                </Button>
                <span className="text-sm text-muted-foreground">{page + 1} / {totalPages}</span>
                <Button variant="outline" size="sm" disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} className="touch-target">
                  Próxima <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          </>
        )}

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader><DialogTitle>{editing ? 'Editar' : 'Novo'} Equipamento</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>TAG</Label><Input value={form.tag} onChange={e => set('tag', e.target.value)} className="touch-target mt-1" /></div>
              <div><Label>Equipamento *</Label><Input value={form.equipamento} onChange={e => set('equipamento', e.target.value)} className="touch-target mt-1" /></div>
              <div><Label>Local</Label><Input value={form.local} onChange={e => set('local', e.target.value)} className="touch-target mt-1" /></div>
              <div><Label>Área</Label>
                <Select value={form.area} onValueChange={v => set('area', v)}>
                  <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Elétrica">Elétrica</SelectItem>
                    <SelectItem value="Mecânica">Mecânica</SelectItem>
                    <SelectItem value="Instrumentação">Instrumentação</SelectItem>
                  </SelectContent>
                </Select>
              </div>
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
  );
};

export default Equipamentos;

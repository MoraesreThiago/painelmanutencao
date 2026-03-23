import { useState } from 'react';
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
import { useEquipamentosPaginated, useInvalidateEquipamentos, EQUIPAMENTOS_PAGE_SIZE } from '@/hooks/queries';
import type { Tables } from '@/integrations/supabase/types';

type EquipamentoView = Tables<'vw_equipamentos_app'>;

const Equipamentos = () => {
  const { profile } = useAuth();
  const isAdmin = profile?.perfil === 'administrador';
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<EquipamentoView | null>(null);
  const [form, setForm] = useState({ tag: '', equipamento: '', local: '', area: 'Elétrica', status: 'Ativo' });

  const invalidate = useInvalidateEquipamentos();
  const { data, isLoading } = useEquipamentosPaginated({ search, page });

  const items = data?.data ?? [];
  const totalCount = data?.totalCount ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalCount / EQUIPAMENTOS_PAGE_SIZE));

  const openNew = () => { setEditing(null); setForm({ tag: '', equipamento: '', local: '', area: 'Elétrica', status: 'Ativo' }); setDialogOpen(true); };
  const openEdit = (e: EquipamentoView) => { setEditing(e); setForm({ tag: e.tag || '', equipamento: e.equipamento || '', local: e.local || '', area: e.area || 'Elétrica', status: e.status || 'Ativo' }); setDialogOpen(true); };

  const handleSave = async () => {
    if (!form.equipamento.trim()) { toast.error('Equipamento é obrigatório'); return; }
    try {
      if (editing) {
        // vw_equipamentos_app doesn't have id — we need to find real equipamento
        // For edit we use the underlying equipamentos table
        const { error } = await supabase.from('equipamentos').update(form).eq('tag', editing.tag!);
        if (error) throw error;
        toast.success('Equipamento atualizado!');
      } else {
        const { error } = await supabase.from('equipamentos').insert(form);
        if (error) throw error;
        toast.success('Equipamento cadastrado!');
      }
      setDialogOpen(false);
      invalidate();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Erro ao salvar');
    }
  };

  const handleDelete = async (tag: string) => {
    if (!confirm('Excluir equipamento?')) return;
    const { error } = await supabase.from('equipamentos').delete().eq('tag', tag);
    if (error) { toast.error('Sem permissão ou erro ao excluir'); return; }
    toast.success('Equipamento excluído!');
    invalidate();
  };

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  return (
    <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-bold">Equipamentos</h1>
          {isAdmin && <Button onClick={openNew} className="touch-target"><Plus className="h-5 w-5 mr-2" /> Novo</Button>}
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Buscar por TAG ou equipamento..." value={search} onChange={e => { setSearch(e.target.value); setPage(0); }} className="pl-10 touch-target" />
        </div>

        {isLoading ? (
          <div className="flex justify-center py-8"><div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" /></div>
        ) : items.length === 0 ? (
          <Card><CardContent className="p-8 text-center text-muted-foreground">Nenhum equipamento encontrado.</CardContent></Card>
        ) : (
          <>
            <div className="space-y-2">
              {items.map((e, i) => (
                <Card key={(e.tag || '') + '-' + i}>
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
                        <Button variant="ghost" size="sm" onClick={() => e.tag && handleDelete(e.tag)} className="touch-target text-destructive"><Trash2 className="h-4 w-4" /></Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="flex items-center justify-between pt-2">
              <p className="text-sm text-muted-foreground">
                {page * EQUIPAMENTOS_PAGE_SIZE + 1}–{Math.min((page + 1) * EQUIPAMENTOS_PAGE_SIZE, totalCount)} de {totalCount}
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

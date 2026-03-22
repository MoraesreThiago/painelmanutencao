import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, Search, RotateCcw, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { isLeaderOrAbove } from '@/lib/roles';
import { format } from 'date-fns';

const PAGE_SIZE = 20;

interface MotorEletrico {
  id: string;
  tag: string;
  motor: string;
  potencia: string | null;
  identificacao_motor: string | null;
  carcaca: string | null;
  fabricante: string | null;
  rpm: string | null;
  tensao: string | null;
  corrente: string | null;
  numero_nf: string;
  data_saida: string | null;
  destino: string | null;
  motivo: string | null;
  status_retorno: string;
  data_retorno: string | null;
  area: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

const MotoresEletricos = () => {
  const navigate = useNavigate();
  const { profile } = useAuth();
  const canDelete = isLeaderOrAbove(profile);

  const [items, setItems] = useState<MotorEletrico[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);

  const load = async () => {
    setLoading(true);
    const from = page * PAGE_SIZE;
    const to = from + PAGE_SIZE - 1;

    let countQuery = (supabase as any).from('motores_eletricos').select('*', { count: 'exact', head: true });
    let dataQuery = (supabase as any).from('motores_eletricos').select('*').order('data_saida', { ascending: false }).range(from, to);

    if (search.trim()) {
      const s = `%${search.trim()}%`;
      const orFilter = `tag.ilike.${s},motor.ilike.${s},numero_nf.ilike.${s}`;
      countQuery = countQuery.or(orFilter);
      dataQuery = dataQuery.or(orFilter);
    }

    const [{ count }, { data }] = await Promise.all([countQuery, dataQuery]);
    setTotalCount(count || 0);
    setItems((data || []) as MotorEletrico[]);
    setLoading(false);
  };

  useEffect(() => { setPage(0); }, [search]);
  useEffect(() => { load(); }, [search, page]);

  const handleDelete = async () => {
    if (!deleteId) return;
    const { error } = await (supabase as any).from('motores_eletricos').delete().eq('id', deleteId);
    setDeleteId(null);
    if (error) {
      toast.error('Erro ao excluir: ' + error.message);
      return;
    }
    toast.success('Registro excluído!');
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

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

  return (
    <>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Serviço Externo — Motores</h1>
            <p className="text-sm text-muted-foreground mt-1">Registro de motores enviados para serviço externo</p>
          </div>
          <Button onClick={() => navigate('/motores-eletricos/novo')}>
            <Plus className="mr-2 h-4 w-4" />Registrar Serviço
          </Button>
        </div>

        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Buscar por tag, equipamento ou NF..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
          </div>
        ) : items.length === 0 ? (
          <Card><CardContent className="py-12 text-center text-muted-foreground">Nenhum registro encontrado.</CardContent></Card>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {items.map(m => (
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
                    {m.identificacao_motor && <p><span className="font-medium text-muted-foreground">MO:</span> {m.identificacao_motor}</p>}
                    {m.carcaca && <p><span className="font-medium text-muted-foreground">Carcaça:</span> {m.carcaca}</p>}
                    {m.fabricante && <p><span className="font-medium text-muted-foreground">Fabricante:</span> {m.fabricante}</p>}
                    {m.potencia && <p><span className="font-medium text-muted-foreground">Potência:</span> {m.potencia}</p>}
                    <p><span className="font-medium text-muted-foreground">NF:</span> {m.numero_nf}</p>
                    <p><span className="font-medium text-muted-foreground">Saída:</span> {format(new Date(m.data_saida + 'T12:00:00'), 'dd/MM/yyyy')}</p>
                    {m.destino && <p><span className="font-medium text-muted-foreground">Destino:</span> {m.destino}</p>}
                    {m.motivo && <p><span className="font-medium text-muted-foreground">Serviço:</span> {m.motivo}</p>}
                    {m.data_retorno && <p><span className="font-medium text-muted-foreground">Retorno:</span> {format(new Date(m.data_retorno + 'T12:00:00'), 'dd/MM/yyyy')}</p>}

                    <div className="flex gap-2 pt-2 border-t">
                      {m.status_retorno === 'Pendente' && (
                        <Button size="sm" variant="outline" onClick={() => handleMarcarRetorno(m)}>
                          <RotateCcw className="mr-1 h-3.5 w-3.5" />Marcar Retorno
                        </Button>
                      )}
                      <Button size="sm" variant="ghost" onClick={() => navigate(`/motores-eletricos/${m.id}`)}>
                        <Edit className="h-3.5 w-3.5" />
                      </Button>
                      {canDelete && (
                        <Button size="sm" variant="ghost" className="text-destructive hover:text-destructive" onClick={() => setDeleteId(m.id)}>
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      )}
                    </div>
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
      </div>

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir registro</AlertDialogTitle>
            <AlertDialogDescription>Deseja excluir este registro de serviço externo? Esta ação não pode ser desfeita.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">Excluir</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default MotoresEletricos;

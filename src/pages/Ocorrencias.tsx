import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Edit, Lock, ChevronLeft, ChevronRight } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import type { Ocorrencia } from '@/types/database';
import { useAuth } from '@/contexts/AuthContext';
import { isAdmin as checkAdmin, canEditWithoutTimeLimit } from '@/lib/roles';

const PAGE_SIZE = 20;

const statusColors: Record<string, string> = {
  Pendente: 'bg-status-pendente text-primary-foreground',
  Liberado: 'bg-status-liberado text-primary-foreground',
  'Em andamento': 'bg-status-andamento text-primary-foreground',
  Realizada: 'bg-status-realizada text-primary-foreground',
};

const Ocorrencias = () => {
  const navigate = useNavigate();
  const { profile } = useAuth();
  const isAdmin = checkAdmin(profile);
  const canEditAnytime = canEditWithoutTimeLimit(profile);
  const [ocorrencias, setOcorrencias] = useState<Ocorrencia[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('todos');
  const [filterArea, setFilterArea] = useState('todos');
  const [filterTurno, setFilterTurno] = useState('todos');
  const [page, setPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);

  const load = async () => {
    setLoading(true);
    const from = page * PAGE_SIZE;
    const to = from + PAGE_SIZE - 1;

    let countQuery = (supabase as any).from('ocorrencias').select('*', { count: 'exact', head: true });
    let dataQuery = (supabase as any).from('ocorrencias').select('*, colaboradores(nome)').order('data_ocorrencia', { ascending: false }).order('created_at', { ascending: false }).range(from, to);

    if (filterStatus !== 'todos') { countQuery = countQuery.eq('status', filterStatus); dataQuery = dataQuery.eq('status', filterStatus); }
    if (filterArea !== 'todos') { countQuery = countQuery.eq('area', filterArea); dataQuery = dataQuery.eq('area', filterArea); }
    if (filterTurno !== 'todos') { countQuery = countQuery.eq('turno', filterTurno); dataQuery = dataQuery.eq('turno', filterTurno); }
    if (search.trim()) {
      const s = `%${search.trim()}%`;
      const orFilter = `tag.ilike.${s},equipamento.ilike.${s},descricao.ilike.${s},area.ilike.${s}`;
      countQuery = countQuery.or(orFilter);
      dataQuery = dataQuery.or(orFilter);
    }

    const [{ count }, { data }] = await Promise.all([countQuery, dataQuery]);
    setTotalCount(count || 0);
    setOcorrencias((data || []) as Ocorrencia[]);
    setLoading(false);
  };

  useEffect(() => { setPage(0); }, [filterStatus, filterArea, filterTurno, search]);
  useEffect(() => { load(); }, [filterStatus, filterArea, filterTurno, search, page]);

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

  return (
    <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-bold">Ocorrências</h1>
          <Button onClick={() => navigate('/ocorrencias/nova')} className="touch-target">
            <Plus className="h-5 w-5 mr-2" /> Nova Ocorrência
          </Button>
        </div>

        <Card>
          <CardContent className="p-4 space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Buscar por TAG, equipamento, descrição..." value={search} onChange={e => setSearch(e.target.value)} className="pl-10 touch-target" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="touch-target"><SelectValue placeholder="Status" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos os Status</SelectItem>
                  <SelectItem value="Pendente">Pendente</SelectItem>
                  <SelectItem value="Liberado">Liberado</SelectItem>
                  <SelectItem value="Em andamento">Em andamento</SelectItem>
                  <SelectItem value="Realizada">Realizada</SelectItem>
                </SelectContent>
              </Select>
              {isAdmin ? (
                <Select value={filterArea} onValueChange={setFilterArea}>
                  <SelectTrigger className="touch-target"><SelectValue placeholder="Área" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todos">Todas as Áreas</SelectItem>
                    <SelectItem value="Elétrica">Elétrica</SelectItem>
                    <SelectItem value="Mecânica">Mecânica</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <Input value={profile?.area || ''} disabled className="touch-target" />
              )}
              <Select value={filterTurno} onValueChange={setFilterTurno}>
                <SelectTrigger className="touch-target"><SelectValue placeholder="Turno" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos os Turnos</SelectItem>
                  <SelectItem value="A">A</SelectItem>
                  <SelectItem value="B">B</SelectItem>
                  <SelectItem value="C">C</SelectItem>
                  <SelectItem value="D">D</SelectItem>
                  <SelectItem value="ADM">ADM</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {loading ? (
          <div className="flex justify-center py-8"><div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" /></div>
        ) : ocorrencias.length === 0 ? (
          <Card><CardContent className="p-8 text-center text-muted-foreground">Nenhuma ocorrência encontrada.</CardContent></Card>
        ) : (
          <>
            <div className="space-y-2">
              {ocorrencias.map(o => (
                <Card key={o.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2 mb-1">
                          <span className="font-semibold">{o.equipamento || 'Sem equipamento'}</span>
                          {o.tag && <Badge variant="outline" className="text-xs">{o.tag}</Badge>}
                          <Badge variant="secondary" className="text-xs">{o.area}</Badge>
                          <Badge variant="secondary" className="text-xs">Turno {o.turno}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground truncate">{o.descricao}</p>
                        <div className="flex flex-wrap items-center gap-2 mt-2 text-xs text-muted-foreground">
                          <span>{o.data_ocorrencia.split('-').reverse().join('/')}</span>
                          <span>•</span>
                          <span>{o.horario}</span>
                          {o.colaboradores?.nome && <><span>•</span><span>{o.colaboradores.nome}</span></>}
                          {o.gerar_os && <Badge className="bg-primary text-primary-foreground text-xs">OS</Badge>}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2 shrink-0">
                        <Badge className={statusColors[o.status] || 'bg-muted'}>{o.status}</Badge>
                        {(() => {
                          const createdAt = new Date(o.created_at || o.data_ocorrencia);
                          const expired = (Date.now() - createdAt.getTime()) > 24 * 60 * 60 * 1000;
                          const canEdit = canEditAnytime || !expired;
                          return canEdit ? (
                            <Button variant="ghost" size="sm" onClick={() => navigate(`/ocorrencias/${o.id}`)} className="touch-target">
                              <Edit className="h-4 w-4" />
                            </Button>
                          ) : (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <span className="inline-flex items-center justify-center h-8 w-8 text-muted-foreground/50 cursor-not-allowed">
                                    <Lock className="h-4 w-4" />
                                  </span>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>Edição bloqueada após 24h</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          );
                        })()}
                      </div>
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
  );
};

export default Ocorrencias;

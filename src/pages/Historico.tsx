import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import type { Ocorrencia } from '@/types/database';
import { STATUS_COLORS, DEFAULT_PAGE_SIZE } from '@/lib/constants';

const Historico = () => {
  const [items, setItems] = useState<Ocorrencia[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Ocorrencia | null>(null);
  const [search, setSearch] = useState('');
  const [filterHorario, setFilterHorario] = useState('todos');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [page, setPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);

  const load = async () => {
    setLoading(true);
    const from = page * DEFAULT_PAGE_SIZE;
    const to = from + DEFAULT_PAGE_SIZE - 1;

    let countQuery = supabase.from('ocorrencias').select('*', { count: 'exact', head: true });
    let dataQuery = supabase.from('ocorrencias').select('*, colaboradores(nome)').order('data_ocorrencia', { ascending: false }).order('created_at', { ascending: false }).range(from, to);

    if (filterHorario !== 'todos') { countQuery = countQuery.eq('horario', filterHorario); dataQuery = dataQuery.eq('horario', filterHorario); }
    if (dateFrom) { countQuery = countQuery.gte('data_ocorrencia', dateFrom); dataQuery = dataQuery.gte('data_ocorrencia', dateFrom); }
    if (dateTo) { countQuery = countQuery.lte('data_ocorrencia', dateTo); dataQuery = dataQuery.lte('data_ocorrencia', dateTo); }
    if (search.trim()) {
      const s = `%${search.trim()}%`;
      const orFilter = `tag.ilike.${s},equipamento.ilike.${s},descricao.ilike.${s}`;
      countQuery = countQuery.or(orFilter);
      dataQuery = dataQuery.or(orFilter);
    }

    const [{ count }, { data }] = await Promise.all([countQuery, dataQuery]);
    setTotalCount(count || 0);
    setItems((data ?? []) as Ocorrencia[]);
    setLoading(false);
  };

  useEffect(() => { setPage(0); }, [filterHorario, dateFrom, dateTo, search]);
  useEffect(() => { load(); }, [filterHorario, dateFrom, dateTo, search, page]);

  const totalPages = Math.max(1, Math.ceil(totalCount / DEFAULT_PAGE_SIZE));

  return (
    <div className="space-y-4">
        <h1 className="text-2xl font-bold">Histórico de Ocorrências</h1>

        <Card>
          <CardContent className="p-4 space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Buscar por TAG, equipamento, descrição..." value={search} onChange={e => setSearch(e.target.value)} className="pl-10 touch-target" />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div>
                <Label className="text-xs">Data inicial</Label>
                <Input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="touch-target mt-1" />
              </div>
              <div>
                <Label className="text-xs">Data final</Label>
                <Input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="touch-target mt-1" />
              </div>
              <div>
                <Label className="text-xs">Horário</Label>
                <Select value={filterHorario} onValueChange={setFilterHorario}>
                  <SelectTrigger className="touch-target mt-1"><SelectValue placeholder="Horário" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todos">Todos</SelectItem>
                    <SelectItem value="Dia">Dia</SelectItem>
                    <SelectItem value="Amanhecida">Amanhecida</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {loading ? (
          <div className="flex justify-center py-8"><div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" /></div>
        ) : items.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">Nenhuma ocorrência encontrada.</p>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {items.map(o => (
                <Card
                  key={o.id}
                  className="cursor-pointer transition-shadow hover:shadow-md hover:border-primary/40 active:scale-[0.98]"
                  onClick={() => setSelected(o)}
                >
                  <CardContent className="p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">{o.data_ocorrencia.split('-').reverse().join('/')}</span>
                      <Badge className={STATUS_COLORS[o.status] || 'bg-muted'}>{o.status}</Badge>
                    </div>
                    <p className="font-medium text-sm leading-snug line-clamp-2">{o.equipamento || o.tag || 'Sem equipamento'}</p>
                    {o.tag && o.equipamento && <span className="text-xs text-muted-foreground">TAG: {o.tag}</span>}
                    <p className="text-xs text-muted-foreground line-clamp-2">{o.descricao}</p>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground pt-1">
                      <Badge variant="secondary" className="text-xs">{o.area}</Badge>
                      <span>Turno: {o.turno} - {o.horario}</span>
                      {o.colaboradores?.nome && <><span>•</span><span>{o.colaboradores.nome}</span></>}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="flex items-center justify-between pt-2">
              <p className="text-sm text-muted-foreground">
                {page * DEFAULT_PAGE_SIZE + 1}–{Math.min((page + 1) * DEFAULT_PAGE_SIZE, totalCount)} de {totalCount}
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

        <Dialog open={!!selected} onOpenChange={() => setSelected(null)}>
          <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
            <DialogHeader><DialogTitle>Detalhes da Ocorrência</DialogTitle></DialogHeader>
            {selected && (
              <div className="space-y-3 text-sm">
                <div className="grid grid-cols-2 gap-2">
                  <div><span className="text-muted-foreground">Data:</span> {selected.data_ocorrencia.split('-').reverse().join('/')}</div>
                  <div><span className="text-muted-foreground">Horário:</span> {selected.horario}</div>
                  <div><span className="text-muted-foreground">Turno:</span> {selected.turno}</div>
                  <div><span className="text-muted-foreground">Área:</span> {selected.area}</div>
                  <div><span className="text-muted-foreground">TAG:</span> {selected.tag || '-'}</div>
                  <div><span className="text-muted-foreground">Equipamento:</span> {selected.equipamento || '-'}</div>
                  <div><span className="text-muted-foreground">Local:</span> {selected.local || '-'}</div>
                  <div><span className="text-muted-foreground">Status:</span> <Badge className={STATUS_COLORS[selected.status]}>{selected.status}</Badge></div>
                </div>
                <div><span className="text-muted-foreground">Descrição:</span><p className="mt-1">{selected.descricao}</p></div>
                {selected.colaboradores?.nome && <div><span className="text-muted-foreground">Colaborador:</span> {selected.colaboradores.nome}</div>}
                {selected.houve_parada && (
                  <div className="border-t pt-2">
                    <p className="font-medium mb-1">Parada</p>
                    <div><span className="text-muted-foreground">Tipo:</span> {selected.tipo_parada}</div>
                    <div><span className="text-muted-foreground">Tempo:</span> {selected.tempo_parada}</div>
                  </div>
                )}
                {selected.gerar_os && (
                  <div className="border-t pt-2">
                    <p className="font-medium mb-1">Ordem de Serviço</p>
                    <div><span className="text-muted-foreground">Prioridade:</span> {selected.prioridade_os}</div>
                    <div><span className="text-muted-foreground">Tipo:</span> {selected.tipo_manutencao_os}</div>
                    {selected.observacao_os && <div><span className="text-muted-foreground">Obs:</span> {selected.observacao_os}</div>}
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
    </div>
  );
};

export default Historico;

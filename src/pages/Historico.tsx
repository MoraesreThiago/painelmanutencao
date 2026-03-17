import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Layout } from '@/components/Layout';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Search, Eye } from 'lucide-react';
import type { Ocorrencia } from '@/types/database';

const statusColors: Record<string, string> = {
  Pendente: 'bg-status-pendente text-primary-foreground',
  Liberado: 'bg-status-liberado text-primary-foreground',
  'Em andamento': 'bg-status-andamento text-primary-foreground',
  Realizada: 'bg-status-realizada text-primary-foreground',
};

const Historico = () => {
  const [items, setItems] = useState<Ocorrencia[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Ocorrencia | null>(null);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('todos');
  const [filterArea, setFilterArea] = useState('todos');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const load = async () => {
    setLoading(true);
    let query = (supabase as any).from('ocorrencias').select('*, colaboradores(nome)').order('data_ocorrencia', { ascending: false });
    if (filterStatus !== 'todos') query = query.eq('status', filterStatus);
    if (filterArea !== 'todos') query = query.eq('area', filterArea);
    if (dateFrom) query = query.gte('data_ocorrencia', dateFrom);
    if (dateTo) query = query.lte('data_ocorrencia', dateTo);
    const { data } = await query;
    setItems((data || []) as Ocorrencia[]);
    setLoading(false);
  };

  useEffect(() => { load(); }, [filterStatus, filterArea, dateFrom, dateTo]);

  const filtered = items.filter(o => {
    if (!search) return true;
    const s = search.toLowerCase();
    return o.tag?.toLowerCase().includes(s) || o.equipamento?.toLowerCase().includes(s) || o.descricao.toLowerCase().includes(s) || o.colaboradores?.nome?.toLowerCase().includes(s);
  });

  return (
    <Layout>
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Histórico de Ocorrências</h1>

        <Card>
          <CardContent className="p-4 space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Buscar por TAG, equipamento, colaborador..." value={search} onChange={e => setSearch(e.target.value)} className="pl-10 touch-target" />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <Label className="text-xs">De</Label>
                <Input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="touch-target mt-1" />
              </div>
              <div>
                <Label className="text-xs">Até</Label>
                <Input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="touch-target mt-1" />
              </div>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="touch-target"><SelectValue placeholder="Status" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  <SelectItem value="Pendente">Pendente</SelectItem>
                  <SelectItem value="Liberado">Liberado</SelectItem>
                  <SelectItem value="Em andamento">Em andamento</SelectItem>
                  <SelectItem value="Realizada">Realizada</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterArea} onValueChange={setFilterArea}>
                <SelectTrigger className="touch-target"><SelectValue placeholder="Área" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todas</SelectItem>
                  <SelectItem value="Elétrica">Elétrica</SelectItem>
                  <SelectItem value="Mecânica">Mecânica</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {loading ? (
          <div className="flex justify-center py-8"><div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left p-3">Data</th>
                  <th className="text-left p-3">TAG</th>
                  <th className="text-left p-3">Equipamento</th>
                  <th className="text-left p-3">Área</th>
                  <th className="text-left p-3">Status</th>
                  <th className="text-left p-3">Turno</th>
                  <th className="p-3"></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(o => (
                  <tr key={o.id} className="border-b hover:bg-muted/30">
                    <td className="p-3">{o.data_ocorrencia.split('-').reverse().join('/')}</td>
                    <td className="p-3">{o.tag || '-'}</td>
                    <td className="p-3">{o.equipamento || '-'}</td>
                    <td className="p-3">{o.area}</td>
                    <td className="p-3"><Badge className={statusColors[o.status] || 'bg-muted'}>{o.status}</Badge></td>
                    <td className="p-3">{o.turno}</td>
                    <td className="p-3"><Button variant="ghost" size="sm" onClick={() => setSelected(o)} className="touch-target"><Eye className="h-4 w-4" /></Button></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && <p className="text-center text-muted-foreground py-8">Nenhuma ocorrência encontrada.</p>}
          </div>
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
                  <div><span className="text-muted-foreground">Status:</span> <Badge className={statusColors[selected.status]}>{selected.status}</Badge></div>
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
    </Layout>
  );
};

export default Historico;

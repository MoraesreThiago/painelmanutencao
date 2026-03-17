import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { FileText, History, Users, BarChart3, Zap, Plus, Clock, CheckCircle2, AlertCircle, PlayCircle, Settings } from 'lucide-react';
import type { Ocorrencia } from '@/types/database';
import { Layout } from '@/components/Layout';
import { Badge } from '@/components/ui/badge';

const statusConfig: Record<string, { color: string; icon: any }> = {
  Pendente: { color: 'bg-status-pendente', icon: AlertCircle },
  Liberado: { color: 'bg-status-liberado', icon: Clock },
  'Em andamento': { color: 'bg-status-andamento', icon: PlayCircle },
  Realizada: { color: 'bg-status-realizada', icon: CheckCircle2 },
};

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({ total: 0, pendentes: 0, liberadas: 0, andamento: 0, realizadas: 0, comOS: 0 });
  const [recent, setRecent] = useState<Ocorrencia[]>([]);

  useEffect(() => {
    const load = async () => {
      const { data: all } = await (supabase as any).from('ocorrencias').select('*').order('created_at', { ascending: false }).limit(5);
      const items = (all || []) as Ocorrencia[];
      setRecent(items);

      const { count: total } = await (supabase as any).from('ocorrencias').select('*', { count: 'exact', head: true });
      const { count: pendentes } = await (supabase as any).from('ocorrencias').select('*', { count: 'exact', head: true }).eq('status', 'Pendente');
      const { count: liberadas } = await (supabase as any).from('ocorrencias').select('*', { count: 'exact', head: true }).eq('status', 'Liberado');
      const { count: andamento } = await (supabase as any).from('ocorrencias').select('*', { count: 'exact', head: true }).eq('status', 'Em andamento');
      const { count: realizadas } = await (supabase as any).from('ocorrencias').select('*', { count: 'exact', head: true }).eq('status', 'Realizada');
      const { count: comOS } = await (supabase as any).from('ocorrencias').select('*', { count: 'exact', head: true }).eq('gerar_os', true);

      setStats({ total: total || 0, pendentes: pendentes || 0, liberadas: liberadas || 0, andamento: andamento || 0, realizadas: realizadas || 0, comOS: comOS || 0 });
    };
    load();
  }, []);

  const statCards = [
    { label: 'Total', value: stats.total, icon: FileText, color: 'text-foreground' },
    { label: 'Pendentes', value: stats.pendentes, icon: AlertCircle, color: 'text-status-pendente' },
    { label: 'Liberadas', value: stats.liberadas, icon: Clock, color: 'text-status-liberado' },
    { label: 'Em Andamento', value: stats.andamento, icon: PlayCircle, color: 'text-status-andamento' },
    { label: 'Realizadas', value: stats.realizadas, icon: CheckCircle2, color: 'text-status-realizada' },
    { label: 'Com OS', value: stats.comOS, icon: Settings, color: 'text-primary' },
  ];

  const shortcuts = [
    { label: 'Nova Ocorrência', icon: Plus, path: '/ocorrencias/nova' },
    { label: 'Histórico', icon: History, path: '/historico' },
    { label: 'Colaboradores', icon: Users, path: '/colaboradores' },
    { label: 'Resumo Mensal', icon: BarChart3, path: '/resumo-mensal' },
    { label: 'Automações', icon: Zap, path: '/automacoes' },
  ];

  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {statCards.map(s => (
            <Card key={s.label} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate('/ocorrencias')}>
              <CardContent className="p-4 flex flex-col items-center text-center">
                <s.icon className={`h-8 w-8 mb-2 ${s.color}`} />
                <p className="text-2xl font-bold">{s.value}</p>
                <p className="text-xs text-muted-foreground">{s.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {shortcuts.map(s => (
            <Button key={s.label} variant="outline" className="h-auto py-4 flex flex-col gap-2 touch-target" onClick={() => navigate(s.path)}>
              <s.icon className="h-6 w-6" />
              <span className="text-xs">{s.label}</span>
            </Button>
          ))}
        </div>

        <Card>
          <CardHeader><CardTitle className="text-lg">Últimas Ocorrências</CardTitle></CardHeader>
          <CardContent>
            {recent.length === 0 ? (
              <p className="text-muted-foreground text-sm">Nenhuma ocorrência registrada.</p>
            ) : (
              <div className="space-y-3">
                {recent.map(o => {
                  const sc = statusConfig[o.status] || statusConfig.Pendente;
                  return (
                    <div key={o.id} className="flex items-center justify-between p-3 rounded-lg border cursor-pointer hover:bg-muted/50" onClick={() => navigate(`/ocorrencias/${o.id}`)}>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-sm truncate">{o.equipamento || o.tag || 'Sem equipamento'}</span>
                          <Badge variant="secondary" className="text-xs">{o.area}</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground truncate">{o.descricao}</p>
                      </div>
                      <Badge className={`${sc.color} text-primary-foreground ml-2 shrink-0`}>{o.status}</Badge>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default Dashboard;

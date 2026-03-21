import { useEffect, useState, useMemo } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { FileText, History, Users, BarChart3, Zap, Plus, AlertCircle } from 'lucide-react';
import type { Ocorrencia } from '@/types/database';

import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';

const DIA_SEQUENCE = ['A', 'D', 'B', 'C'];
const AMAN_SEQUENCE = ['B', 'C', 'A', 'D'];
const REFERENCE_DATE = new Date(2026, 1, 18); // 18/02/2026

function getSlotIndex(diffDays: number): number {
  const cycleDay = ((diffDays % 8) + 8) % 8;
  return Math.floor(cycleDay / 2);
}

function getCurrentAndPreviousTurno(): { currentTurno: string; currentHorario: string; previousTurno: string; previousHorario: string } {
  const now = new Date();
  const hours = now.getHours();
  const minutes = now.getMinutes();
  const currentTime = hours * 60 + minutes;

  const isDia = currentTime >= 430 && currentTime < 1150; // 07:10-19:10

  // Dia operacional: antes das 07:10 ainda pertence ao dia anterior
  const operationalDate = currentTime >= 430
    ? new Date(now.getFullYear(), now.getMonth(), now.getDate())
    : new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
  const diffMs = operationalDate.getTime() - REFERENCE_DATE.getTime();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

  const todaySlot = getSlotIndex(diffDays);
  const yesterdaySlot = getSlotIndex(diffDays - 1);

  if (isDia) {
    return {
      currentTurno: DIA_SEQUENCE[todaySlot],
      currentHorario: 'Dia',
      previousTurno: AMAN_SEQUENCE[yesterdaySlot],
      previousHorario: 'Amanhecida',
    };
  } else {
    return {
      currentTurno: AMAN_SEQUENCE[todaySlot],
      currentHorario: 'Amanhecida',
      previousTurno: DIA_SEQUENCE[todaySlot],
      previousHorario: 'Dia',
    };
  }
}

const statusColors: Record<string, string> = {
  Pendente: 'bg-status-pendente text-primary-foreground',
  Liberado: 'bg-status-liberado text-primary-foreground',
  'Em andamento': 'bg-status-andamento text-primary-foreground',
  Realizada: 'bg-status-realizada text-primary-foreground',
};

const Dashboard = () => {
  const navigate = useNavigate();
  const { profile } = useAuth();
  const [stats, setStats] = useState({ total: 0, pendentes: 0 });
  const [previousOcorrencias, setPreviousOcorrencias] = useState<Ocorrencia[]>([]);

  const turnoInfo = useMemo(() => getCurrentAndPreviousTurno(), []);

  useEffect(() => {
    const load = async () => {
      const { count: total } = await (supabase as any).from('ocorrencias').select('*', { count: 'exact', head: true });
      const { count: pendentes } = await (supabase as any).from('ocorrencias').select('*', { count: 'exact', head: true }).eq('status', 'Pendente');
      setStats({ total: total || 0, pendentes: pendentes || 0 });

      // A partir das 07:10 considera o dia atual; antes disso, o dia anterior
      const now = new Date();
      const currentMinutes = now.getHours() * 60 + now.getMinutes();
      const referenceDate = currentMinutes >= 430
        ? new Date(now.getFullYear(), now.getMonth(), now.getDate())
        : new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
      const todayStr = referenceDate.toISOString().split('T')[0];
      const yesterdayStr = new Date(referenceDate.getTime() - 86400000).toISOString().split('T')[0];

      const { data } = await (supabase as any)
        .from('ocorrencias')
        .select('*, colaboradores(nome)')
        .eq('turno', turnoInfo.previousTurno)
        .eq('horario', turnoInfo.previousHorario)
        .in('data_ocorrencia', [todayStr, yesterdayStr])
        .order('created_at', { ascending: false })
        .limit(10);

      setPreviousOcorrencias((data || []) as Ocorrencia[]);
    };
    load();
  }, [turnoInfo]);

  const shortcuts = [
    { label: 'Nova Ocorrência', icon: Plus, path: '/ocorrencias/nova' },
    { label: 'Ocorrências', icon: FileText, path: '/ocorrencias' },
    { label: 'Histórico', icon: History, path: '/historico' },
    { label: 'Colaboradores', icon: Users, path: '/colaboradores' },
    { label: 'Resumo Mensal', icon: BarChart3, path: '/resumo-mensal' },
    { label: 'Automações', icon: Zap, path: '/automacoes' },
  ];

  return (
    <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <p className="text-sm text-muted-foreground">
              Turno atual: <span className="font-medium text-foreground">{turnoInfo.currentTurno}</span> — {turnoInfo.currentHorario}
              {profile?.area && <> • {profile.area}</>}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate('/ocorrencias')}>
            <CardContent className="p-4 flex flex-col items-center text-center">
              <FileText className="h-8 w-8 mb-2 text-foreground" />
              <p className="text-2xl font-bold">{stats.total}</p>
              <p className="text-xs text-muted-foreground">Total de Ocorrências</p>
            </CardContent>
          </Card>
          <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate('/ocorrencias')}>
            <CardContent className="p-4 flex flex-col items-center text-center">
              <AlertCircle className="h-8 w-8 mb-2 text-status-pendente" />
              <p className="text-2xl font-bold">{stats.pendentes}</p>
              <p className="text-xs text-muted-foreground">Pendentes</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
          {shortcuts.map(s => (
            <Button key={s.label} variant="outline" className="h-auto py-4 flex flex-col gap-2 touch-target" onClick={() => navigate(s.path)}>
              <s.icon className="h-6 w-6" />
              <span className="text-xs">{s.label}</span>
            </Button>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Ocorrências do Turno Anterior</CardTitle>
            <p className="text-xs text-muted-foreground">
              Turno {turnoInfo.previousTurno} — {turnoInfo.previousHorario}
            </p>
          </CardHeader>
          <CardContent>
            {previousOcorrencias.length === 0 ? (
              <p className="text-muted-foreground text-sm">Nenhuma ocorrência registrada no turno anterior.</p>
            ) : (
              <div className="space-y-2">
                {previousOcorrencias.map(o => (
                  <div key={o.id} className="flex items-center justify-between p-3 rounded-lg border bg-muted/30">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm truncate">{o.equipamento || o.tag || 'Sem equipamento'}</span>
                        {o.tag && <Badge variant="outline" className="text-xs">{o.tag}</Badge>}
                      </div>
                      <p className="text-xs text-muted-foreground truncate">{o.descricao}</p>
                      <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        {o.colaboradores?.nome && <span>{o.colaboradores.nome}</span>}
                        {o.local && <><span>•</span><span>{o.local}</span></>}
                      </div>
                    </div>
                    <Badge className={`${statusColors[o.status] || 'bg-muted'} ml-2 shrink-0`}>{o.status}</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
    </div>
  );
};

export default Dashboard;

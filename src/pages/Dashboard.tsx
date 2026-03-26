import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useNavigate } from 'react-router-dom';
import { FileText, History, Users, BarChart3, Zap, Plus } from 'lucide-react';
import type { Ocorrencia } from '@/types/database';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { canManageColaboradores } from '@/lib/roles';
import { useTurnoOcorrencias } from '@/hooks/queries';
import { STATUS_COLORS, DIA_SEQUENCE, AMAN_SEQUENCE, REFERENCE_DATE } from '@/lib/constants';

function getSlotIndex(diffDays: number): number {
  const cycleDay = ((diffDays % 8) + 8) % 8;
  return Math.floor(cycleDay / 2);
}

function getCurrentAndPreviousTurno() {
  const now = new Date();
  const currentTime = now.getHours() * 60 + now.getMinutes();
  const isDia = currentTime >= 430 && currentTime < 1150;

  const operationalDate = currentTime >= 430
    ? new Date(now.getFullYear(), now.getMonth(), now.getDate())
    : new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
  const diffDays = Math.round((operationalDate.getTime() - REFERENCE_DATE.getTime()) / (1000 * 60 * 60 * 24));

  const todaySlot = getSlotIndex(diffDays);
  const yesterdaySlot = getSlotIndex(diffDays - 1);

  const todayStr = operationalDate.toISOString().split('T')[0];
  const yesterdayStr = new Date(operationalDate.getTime() - 86400000).toISOString().split('T')[0];

  if (isDia) {
    return {
      currentTurno: DIA_SEQUENCE[todaySlot],
      currentHorario: 'Dia',
      currentDate: todayStr,
      previousTurno: AMAN_SEQUENCE[yesterdaySlot],
      previousHorario: 'Amanhecida',
      previousDate: yesterdayStr,
    };
  }
  return {
    currentTurno: AMAN_SEQUENCE[todaySlot],
    currentHorario: 'Amanhecida',
    currentDate: todayStr,
    previousTurno: DIA_SEQUENCE[todaySlot],
    previousHorario: 'Dia',
    previousDate: todayStr,
  };
}

const OcorrenciaItem = ({ o }: { o: Ocorrencia }) => (
  <div className="flex items-center justify-between p-3 rounded-lg border bg-muted/30">
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
    <Badge className={`${STATUS_COLORS[o.status] || 'bg-muted'} ml-2 shrink-0`}>{o.status}</Badge>
  </div>
);

const Dashboard = () => {
  const navigate = useNavigate();
  const { profile } = useAuth();
  const turnoInfo = useMemo(() => getCurrentAndPreviousTurno(), []);

  const { data: previousOcorrencias = [] } = useTurnoOcorrencias({
    turno: turnoInfo.previousTurno,
    horario: turnoInfo.previousHorario,
    dates: [],
    exactDate: turnoInfo.previousDate,
  });

  const { data: currentOcorrencias = [] } = useTurnoOcorrencias({
    turno: turnoInfo.currentTurno,
    horario: turnoInfo.currentHorario,
    dates: [],
    exactDate: turnoInfo.currentDate,
  });

  const shortcuts = [
    { label: 'Nova Ocorrência', icon: Plus, path: '/ocorrencias/nova' },
    { label: 'Ocorrências', icon: FileText, path: '/ocorrencias' },
    { label: 'Histórico', icon: History, path: '/historico' },
    ...(canManageColaboradores(profile) ? [{ label: 'Colaboradores', icon: Users, path: '/colaboradores' }] : []),
    { label: 'Resumo Mensal', icon: BarChart3, path: '/resumo-mensal' },
    { label: 'Automações', icon: Zap, path: '/automacoes' },
  ];

  return (
    <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">Painel Principal</h1>
            <p className="text-sm text-muted-foreground">
              Turno atual: <span className="font-medium text-foreground">{turnoInfo.currentTurno}</span> — {turnoInfo.currentHorario}
              {profile?.area && <> • {profile.area}</>}
            </p>
          </div>
        </div>

        <div className={`grid gap-3 ${shortcuts.length <= 5 ? 'grid-cols-3 md:grid-cols-5' : 'grid-cols-3 md:grid-cols-6'}`}>
          {shortcuts.map(s => (
            <Button key={s.label} variant="outline" className="h-auto py-4 flex flex-col gap-2 touch-target" onClick={() => navigate(s.path)}>
              <s.icon className="h-6 w-6" />
              <span className="text-xs">{s.label}</span>
            </Button>
          ))}
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Ocorrências por Turno</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="atual">
              <TabsList className="w-full">
                <TabsTrigger value="atual" className="flex-1">
                  Turno Atual ({turnoInfo.currentTurno} — {turnoInfo.currentHorario})
                </TabsTrigger>
                <TabsTrigger value="anterior" className="flex-1">
                  Turno Anterior ({turnoInfo.previousTurno} — {turnoInfo.previousHorario})
                </TabsTrigger>
              </TabsList>
              <TabsContent value="atual" className="mt-3">
                {currentOcorrencias.length === 0 ? (
                  <p className="text-muted-foreground text-sm py-4 text-center">Nenhuma ocorrência registrada no turno atual.</p>
                ) : (
                  <div className="space-y-2">
                    {currentOcorrencias.map(o => <OcorrenciaItem key={o.id} o={o} />)}
                  </div>
                )}
              </TabsContent>
              <TabsContent value="anterior" className="mt-3">
                {previousOcorrencias.length === 0 ? (
                  <p className="text-muted-foreground text-sm py-4 text-center">Nenhuma ocorrência registrada no turno anterior.</p>
                ) : (
                  <div className="space-y-2">
                    {previousOcorrencias.map(o => <OcorrenciaItem key={o.id} o={o} />)}
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
    </div>
  );
};

export default Dashboard;

import { useEffect, useState, useMemo } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Layout } from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import type { Ocorrencia } from '@/types/database';
import { useAuth } from '@/contexts/AuthContext';
import { FilterX } from 'lucide-react';

const COLORS = ['hsl(215,65%,42%)', 'hsl(152,55%,42%)', 'hsl(38,92%,50%)', 'hsl(25,95%,53%)', 'hsl(340,65%,50%)', 'hsl(280,50%,50%)'];

const ResumoMensal = () => {
  const { profile } = useAuth();
  const isAdmin = profile?.perfil === 'administrador';
  const [ocorrencias, setOcorrencias] = useState<Ocorrencia[]>([]);
  const [month, setMonth] = useState(() => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`; });
  const [selectedTurno, setSelectedTurno] = useState<string | null>(null);
  const [selectedLocal, setSelectedLocal] = useState<string | null>(null);
  const [selectedEquipamento, setSelectedEquipamento] = useState<string | null>(null);

  useEffect(() => {
    const [year, mo] = month.split('-').map(Number);
    const start = `${year}-${String(mo).padStart(2, '0')}-01`;
    const lastDay = new Date(year, mo, 0).getDate();
    const end = `${year}-${String(mo).padStart(2, '0')}-${lastDay}`;

    (supabase as any).from('ocorrencias').select('*').gte('data_ocorrencia', start).lte('data_ocorrencia', end)
      .then(({ data }: any) => { setOcorrencias((data || []) as Ocorrencia[]); clearFilters(); });
  }, [month]);

  const hasFilters = selectedTurno || selectedLocal || selectedEquipamento;

  const clearFilters = () => {
    setSelectedTurno(null);
    setSelectedLocal(null);
    setSelectedEquipamento(null);
  };

  const total = ocorrencias.length;
  const paradas = ocorrencias.filter(o => o.houve_parada);
  const pendentes = ocorrencias.filter(o => o.status === 'Pendente').length;

  const porArea = isAdmin
    ? ['Elétrica', 'Mecânica'].map(a => ({ name: a, value: ocorrencias.filter(o => o.area === a).length }))
    : null;

  // Cross-filtered data
  const filteredOcorrencias = useMemo(() => {
    let result = ocorrencias;
    if (selectedTurno) result = result.filter(o => o.turno === selectedTurno);
    if (selectedLocal) result = result.filter(o => o.local === selectedLocal);
    if (selectedEquipamento) result = result.filter(o => o.equipamento === selectedEquipamento);
    return result;
  }, [ocorrencias, selectedTurno, selectedLocal, selectedEquipamento]);

  // Turno data (not filtered by turno itself, but by local/equipamento)
  const turnoFiltered = useMemo(() => {
    let result = ocorrencias;
    if (selectedLocal) result = result.filter(o => o.local === selectedLocal);
    if (selectedEquipamento) result = result.filter(o => o.equipamento === selectedEquipamento);
    return result;
  }, [ocorrencias, selectedLocal, selectedEquipamento]);

  const porTurno = ['A', 'B', 'C', 'D'].map(t => ({ name: `Turno ${t}`, turno: t, value: turnoFiltered.filter(o => o.turno === t).length }));

  // Local data (not filtered by local itself, but by turno/equipamento)
  const localFiltered = useMemo(() => {
    let result = ocorrencias;
    if (selectedTurno) result = result.filter(o => o.turno === selectedTurno);
    if (selectedEquipamento) result = result.filter(o => o.equipamento === selectedEquipamento);
    return result;
  }, [ocorrencias, selectedTurno, selectedEquipamento]);

  const localCount: Record<string, number> = {};
  localFiltered.forEach(o => { if (o.local) localCount[o.local] = (localCount[o.local] || 0) + 1; });
  const topLocais = Object.entries(localCount).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([name, value]) => ({ name, value }));

  // Equipamento data (not filtered by equipamento itself, but by turno/local)
  const eqFiltered = useMemo(() => {
    let result = ocorrencias;
    if (selectedTurno) result = result.filter(o => o.turno === selectedTurno);
    if (selectedLocal) result = result.filter(o => o.local === selectedLocal);
    return result;
  }, [ocorrencias, selectedTurno, selectedLocal]);

  const eqCount: Record<string, number> = {};
  eqFiltered.forEach(o => { if (o.equipamento) eqCount[o.equipamento] = (eqCount[o.equipamento] || 0) + 1; });
  const topEquipamentos = Object.entries(eqCount).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([name, value]) => ({ name, value }));

  const months = Array.from({ length: 12 }, (_, i) => {
    const d = new Date(); d.setMonth(d.getMonth() - i);
    return { value: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`, label: d.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' }) };
  });

  const handleTurnoClick = (data: any) => {
    if (!data?.activePayload?.[0]) return;
    const turno = data.activePayload[0].payload.turno;
    setSelectedTurno(prev => prev === turno ? null : turno);
  };

  const handleLocalClick = (_: any, index: number) => {
    const local = topLocais[index]?.name;
    if (!local) return;
    setSelectedLocal(prev => prev === local ? null : local);
  };

  const handleEquipamentoClick = (data: any) => {
    if (!data?.activePayload?.[0]) return;
    const eq = data.activePayload[0].payload.name;
    setSelectedEquipamento(prev => prev === eq ? null : eq);
  };

  const activeFilters: string[] = [];
  if (selectedTurno) activeFilters.push(`Turno ${selectedTurno}`);
  if (selectedLocal) activeFilters.push(selectedLocal.length > 20 ? selectedLocal.slice(0, 18) + '…' : selectedLocal);
  if (selectedEquipamento) activeFilters.push(selectedEquipamento.length > 20 ? selectedEquipamento.slice(0, 18) + '…' : selectedEquipamento);

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, name, value, percent }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = outerRadius + 20;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);
    if (percent < 0.05) return null;
    const displayName = name.length > 12 ? name.slice(0, 10) + '…' : name;
    return (
      <text x={x} y={y} fill="hsl(var(--foreground))" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize={11}>
        {displayName} ({value})
      </text>
    );
  };

  return (
    <Layout>
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-bold">Resumo Mensal {!isAdmin && profile?.area ? `— ${profile.area}` : ''}</h1>
          <div className="flex items-center gap-2">
            <Select value={month} onValueChange={setMonth}>
              <SelectTrigger className="w-48 touch-target"><SelectValue /></SelectTrigger>
              <SelectContent>{months.map(m => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
        </div>

        {hasFilters && (
          <div className="flex flex-wrap items-center gap-2 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2">
            <span className="text-xs font-medium text-muted-foreground">Filtros ativos:</span>
            {activeFilters.map(f => (
              <Badge key={f} variant="secondary" className="text-xs">{f}</Badge>
            ))}
            <Button variant="ghost" size="sm" onClick={clearFilters} className="ml-auto h-7 text-xs text-destructive hover:text-destructive">
              <FilterX className="h-3.5 w-3.5 mr-1" /> Limpar filtros
            </Button>
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Total de Ocorrências', value: total, filtered: filteredOcorrencias.length },
            { label: 'Paradas', value: paradas.length, filtered: filteredOcorrencias.filter(o => o.houve_parada).length },
            { label: 'Pendentes', value: pendentes, filtered: filteredOcorrencias.filter(o => o.status === 'Pendente').length },
            { label: 'Com OS', value: ocorrencias.filter(o => o.gerar_os).length, filtered: filteredOcorrencias.filter(o => o.gerar_os).length },
          ].map(s => (
            <Card key={s.label}>
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold">{hasFilters ? s.filtered : s.value}</p>
                {hasFilters && s.filtered !== s.value && (
                  <p className="text-xs text-muted-foreground">de {s.value}</p>
                )}
                <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {porArea && (
            <Card>
              <CardHeader><CardTitle className="text-base">Por Área</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={porArea} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                      {porArea.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Por Turno</CardTitle>
              <p className="text-xs text-muted-foreground">Clique para filtrar</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={porTurno} onClick={handleTurnoClick} className="cursor-pointer">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" fontSize={12} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {porTurno.map((entry) => (
                      <Cell
                        key={entry.turno}
                        fill={selectedTurno === entry.turno ? 'hsl(215,65%,32%)' : selectedTurno ? 'hsl(215,30%,75%)' : 'hsl(215,65%,42%)'}
                        stroke={selectedTurno === entry.turno ? 'hsl(215,65%,22%)' : 'none'}
                        strokeWidth={selectedTurno === entry.turno ? 2 : 0}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {topLocais.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Locais com Mais Chamados</CardTitle>
                <p className="text-xs text-muted-foreground">Clique para filtrar</p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={topLocais}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={80}
                      dataKey="value"
                      label={renderCustomLabel}
                      onClick={handleLocalClick}
                      className="cursor-pointer"
                      paddingAngle={2}
                      strokeWidth={2}
                      stroke="hsl(var(--card))"
                    >
                      {topLocais.map((entry, i) => (
                        <Cell
                          key={entry.name}
                          fill={COLORS[i % COLORS.length]}
                          opacity={selectedLocal && selectedLocal !== entry.name ? 0.35 : 1}
                          strokeWidth={selectedLocal === entry.name ? 3 : 2}
                          stroke={selectedLocal === entry.name ? 'hsl(var(--foreground))' : 'hsl(var(--card))'}
                        />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number, name: string) => [value, name]} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </div>

        {topEquipamentos.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Equipamentos com Mais Ocorrências</CardTitle>
              <p className="text-xs text-muted-foreground">Clique para filtrar</p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={Math.max(200, topEquipamentos.length * 45)}>
                <BarChart data={topEquipamentos} layout="vertical" margin={{ left: 20 }} onClick={handleEquipamentoClick} className="cursor-pointer">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" allowDecimals={false} />
                  <YAxis
                    dataKey="name"
                    type="category"
                    width={180}
                    fontSize={11}
                    tickFormatter={(v: string) => v.length > 25 ? v.slice(0, 23) + '…' : v}
                  />
                  <Tooltip />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {topEquipamentos.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={selectedEquipamento === entry.name ? 'hsl(152,55%,32%)' : selectedEquipamento ? 'hsl(152,20%,75%)' : 'hsl(152,55%,42%)'}
                        stroke={selectedEquipamento === entry.name ? 'hsl(152,55%,22%)' : 'none'}
                        strokeWidth={selectedEquipamento === entry.name ? 2 : 0}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
};

export default ResumoMensal;

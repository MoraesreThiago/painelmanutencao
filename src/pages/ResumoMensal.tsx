import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Layout } from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import type { Ocorrencia } from '@/types/database';
import { useAuth } from '@/contexts/AuthContext';

const COLORS = ['hsl(215,65%,42%)', 'hsl(152,55%,42%)', 'hsl(38,92%,50%)', 'hsl(25,95%,53%)', 'hsl(340,65%,50%)'];

const ResumoMensal = () => {
  const { profile } = useAuth();
  const isAdmin = profile?.perfil === 'administrador';
  const [ocorrencias, setOcorrencias] = useState<Ocorrencia[]>([]);
  const [month, setMonth] = useState(() => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`; });

  useEffect(() => {
    const [year, mo] = month.split('-').map(Number);
    const start = `${year}-${String(mo).padStart(2, '0')}-01`;
    const lastDay = new Date(year, mo, 0).getDate();
    const end = `${year}-${String(mo).padStart(2, '0')}-${lastDay}`;

    // RLS already filters by area for non-admin users
    (supabase as any).from('ocorrencias').select('*').gte('data_ocorrencia', start).lte('data_ocorrencia', end)
      .then(({ data }: any) => setOcorrencias((data || []) as Ocorrencia[]));
  }, [month]);

  const total = ocorrencias.length;
  const porTurno = ['A', 'B', 'C', 'D', 'ADM'].map(t => ({ name: `Turno ${t}`, value: ocorrencias.filter(o => o.turno === t).length }));
  const paradas = ocorrencias.filter(o => o.houve_parada);
  const pendentes = ocorrencias.filter(o => o.status === 'Pendente').length;

  // Only show "Por Área" chart for admins (non-admins only see their own area)
  const porArea = isAdmin
    ? ['Elétrica', 'Mecânica'].map(a => ({ name: a, value: ocorrencias.filter(o => o.area === a).length }))
    : null;

  const eqCount: Record<string, number> = {};
  ocorrencias.forEach(o => { if (o.equipamento) eqCount[o.equipamento] = (eqCount[o.equipamento] || 0) + 1; });
  const topEquipamentos = Object.entries(eqCount).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([name, value]) => ({ name, value }));

  const months = Array.from({ length: 12 }, (_, i) => {
    const d = new Date(); d.setMonth(d.getMonth() - i);
    return { value: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`, label: d.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' }) };
  });

  return (
    <Layout>
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-bold">Resumo Mensal {!isAdmin && profile?.area ? `— ${profile.area}` : ''}</h1>
          <Select value={month} onValueChange={setMonth}>
            <SelectTrigger className="w-48 touch-target"><SelectValue /></SelectTrigger>
            <SelectContent>{months.map(m => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Total de Ocorrências', value: total },
            { label: 'Paradas', value: paradas.length },
            { label: 'Pendentes', value: pendentes },
            { label: 'Com OS', value: ocorrencias.filter(o => o.gerar_os).length },
          ].map(s => (
            <Card key={s.label}>
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold">{s.value}</p>
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
            <CardHeader><CardTitle className="text-base">Por Turno</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={porTurno}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" fontSize={12} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="hsl(215,65%,42%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {topEquipamentos.length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-base">Equipamentos com Mais Ocorrências</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={topEquipamentos} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={150} fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="value" fill="hsl(152,55%,42%)" radius={[0, 4, 4, 0]} />
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

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, Search, RotateCcw } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { format } from 'date-fns';

interface MotorEletrico {
  id: string;
  tag: string;
  motor: string;
  potencia: string | null;
  identificacao_motor: string | null;
  carcaca: string | null;
  fabricante: string | null;
  numero_nf: string;
  data_saida: string;
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
  const isAdmin = profile?.perfil === 'administrador';

  const [items, setItems] = useState<MotorEletrico[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const load = async () => {
    setLoading(true);
    const { data } = await (supabase as any)
      .from('motores_eletricos')
      .select('*')
      .order('data_saida', { ascending: false });
    setItems((data || []) as MotorEletrico[]);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Deseja excluir este registro?')) return;
    await (supabase as any).from('motores_eletricos').delete().eq('id', id);
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

  const filtered = items.filter(m =>
    m.tag.toLowerCase().includes(search.toLowerCase()) ||
    m.motor.toLowerCase().includes(search.toLowerCase()) ||
    m.numero_nf.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Layout>
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
        ) : filtered.length === 0 ? (
          <Card><CardContent className="py-12 text-center text-muted-foreground">Nenhum registro encontrado.</CardContent></Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filtered.map(m => (
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
                    {isAdmin && (
                      <Button size="sm" variant="ghost" className="text-destructive hover:text-destructive" onClick={() => handleDelete(m.id)}>
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default MotoresEletricos;

import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { isAdmin } from '@/lib/roles';
import { Navigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Plus, Users, Shield } from 'lucide-react';
import { toast } from 'sonner';
import { getRoleLabel } from '@/lib/roles';

interface UserProfile {
  id: string;
  nome: string | null;
  email: string | null;
  perfil: string | null;
  area: string | null;
}

const perfilAreaMap: Record<string, string> = {
  administrador: '',
  manutencao_eletrica: 'Elétrica',
  manutencao_mecanica: 'Mecânica',
  lider_eletrica: 'Elétrica',
  lider_mecanica: 'Mecânica',
  supervisor_eletrica: 'Elétrica',
  supervisor_mecanica: 'Mecânica',
};

const GerenciarUsuarios = () => {
  const { profile } = useAuth();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    email: '',
    password: '',
    nome: '',
    perfil: '',
    area: '',
  });

  if (!isAdmin(profile)) return <Navigate to="/dashboard" replace />;

  const loadUsers = async () => {
    setLoading(true);
    const { data } = await (supabase as any).from('profiles').select('*').order('nome');
    setUsers(data || []);
    setLoading(false);
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const set = (key: string, value: string) => {
    if (key === 'perfil') {
      const area = perfilAreaMap[value] || '';
      setForm(f => ({ ...f, perfil: value, area }));
    } else {
      setForm(f => ({ ...f, [key]: value }));
    }
  };

  const handleCreate = async () => {
    if (!form.email || !form.password || !form.nome || !form.perfil) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }
    if (form.password.length < 6) {
      toast.error('A senha deve ter pelo menos 6 caracteres');
      return;
    }

    const area = form.perfil === 'administrador' ? 'Administração' : form.area;
    if (!area) {
      toast.error('Área é obrigatória');
      return;
    }

    setSaving(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const response = await supabase.functions.invoke('create-user', {
        body: {
          email: form.email,
          password: form.password,
          nome: form.nome,
          perfil: form.perfil,
          area,
        },
      });

      if (response.error) {
        throw new Error(response.error.message || 'Erro ao criar usuário');
      }

      if (response.data?.error) {
        throw new Error(response.data.error);
      }

      toast.success('Usuário criado com sucesso!');
      setDialogOpen(false);
      setForm({ email: '', password: '', nome: '', perfil: '', area: '' });
      loadUsers();
    } catch (err: any) {
      toast.error(err.message || 'Erro ao criar usuário');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Gerenciar Usuários</h1>
          <p className="text-sm text-muted-foreground mt-1">Crie e gerencie os acessos ao sistema</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="touch-target">
          <Plus className="h-5 w-5 mr-2" /> Novo Usuário
        </Button>
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="space-y-2">
          {users.map(u => (
            <Card key={u.id}>
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    {u.perfil === 'administrador' ? (
                      <Shield className="h-4 w-4 text-primary" />
                    ) : (
                      <Users className="h-4 w-4 text-primary" />
                    )}
                  </div>
                  <div>
                    <p className="font-semibold">{u.nome || u.email}</p>
                    <p className="text-xs text-muted-foreground">{u.email}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">{getRoleLabel(u.perfil)}</Badge>
                  {u.area && <Badge variant="outline">{u.area}</Badge>}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Criar Novo Usuário</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Nome *</Label>
              <Input value={form.nome} onChange={e => set('nome', e.target.value)} placeholder="Nome completo" className="touch-target mt-1" />
            </div>
            <div>
              <Label>Email *</Label>
              <Input type="email" value={form.email} onChange={e => set('email', e.target.value)} placeholder="email@exemplo.com" className="touch-target mt-1" />
            </div>
            <div>
              <Label>Senha *</Label>
              <Input type="password" value={form.password} onChange={e => set('password', e.target.value)} placeholder="Mínimo 6 caracteres" className="touch-target mt-1" />
            </div>
            <div>
              <Label>Perfil *</Label>
              <Select value={form.perfil} onValueChange={v => set('perfil', v)}>
                <SelectTrigger className="touch-target mt-1"><SelectValue placeholder="Selecione o perfil" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="administrador">Administrador</SelectItem>
                  <SelectItem value="lider_eletrica">Líder Elétrica</SelectItem>
                  <SelectItem value="lider_mecanica">Líder Mecânica</SelectItem>
                  <SelectItem value="supervisor_eletrica">Supervisor Elétrica</SelectItem>
                  <SelectItem value="supervisor_mecanica">Supervisor Mecânica</SelectItem>
                  <SelectItem value="manutencao_eletrica">Manutenção Elétrica</SelectItem>
                  <SelectItem value="manutencao_mecanica">Manutenção Mecânica</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {form.perfil && form.perfil !== 'administrador' && (
              <div>
                <Label>Área</Label>
                <Input value={form.area} disabled className="touch-target mt-1 bg-muted" />
              </div>
            )}
            <Button onClick={handleCreate} disabled={saving} className="w-full touch-target">
              {saving ? 'Criando...' : 'Criar Usuário'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GerenciarUsuarios;

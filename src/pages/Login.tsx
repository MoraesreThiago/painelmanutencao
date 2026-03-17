import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Navigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Wrench } from 'lucide-react';
import { toast } from 'sonner';

const Login = () => {
  const { user, signIn, signUp } = useAuth();
  const [loading, setLoading] = useState(false);

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupNome, setSignupNome] = useState('');
  const [signupPerfil, setSignupPerfil] = useState('');
  const [signupArea, setSignupArea] = useState('');

  if (user) return <Navigate to="/dashboard" replace />;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await signIn(loginEmail, loginPassword);
      toast.success('Login realizado com sucesso!');
    } catch (err: any) {
      toast.error(err.message || 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!signupPerfil) { toast.error('Selecione um perfil'); return; }
    setLoading(true);
    try {
      await signUp(signupEmail, signupPassword, signupNome, signupPerfil, signupArea || '');
      toast.success('Cadastro realizado! Verifique seu email para confirmar.');
    } catch (err: any) {
      toast.error(err.message || 'Erro ao cadastrar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-3">
            <div className="h-14 w-14 rounded-xl bg-primary flex items-center justify-center">
              <Wrench className="h-8 w-8 text-primary-foreground" />
            </div>
          </div>
          <CardTitle className="text-2xl">ManutençãoPro</CardTitle>
          <CardDescription>Sistema de Gestão de Manutenção Industrial</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="login">
            <TabsList className="grid w-full grid-cols-2 mb-4">
              <TabsTrigger value="login" className="touch-target data-[state=active]:shadow-none">Entrar</TabsTrigger>
              <TabsTrigger value="signup" className="touch-target data-[state=active]:shadow-none">Cadastrar</TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <Label htmlFor="login-email">Email</Label>
                  <Input id="login-email" type="email" value={loginEmail} onChange={e => setLoginEmail(e.target.value)} required className="touch-target mt-1" />
                </div>
                <div>
                  <Label htmlFor="login-password">Senha</Label>
                  <Input id="login-password" type="password" value={loginPassword} onChange={e => setLoginPassword(e.target.value)} required className="touch-target mt-1" />
                </div>
                <Button type="submit" className="w-full touch-target text-base" disabled={loading}>
                  {loading ? 'Entrando...' : 'Entrar'}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="signup">
              <form onSubmit={handleSignup} className="space-y-4">
                <div>
                  <Label>Nome</Label>
                  <Input value={signupNome} onChange={e => setSignupNome(e.target.value)} required className="touch-target mt-1" />
                </div>
                <div>
                  <Label>Email</Label>
                  <Input type="email" value={signupEmail} onChange={e => setSignupEmail(e.target.value)} required className="touch-target mt-1" />
                </div>
                <div>
                  <Label>Senha</Label>
                  <Input type="password" value={signupPassword} onChange={e => setSignupPassword(e.target.value)} required minLength={6} className="touch-target mt-1" />
                </div>
                <div>
                  <Label>Perfil</Label>
                  <Select value={signupPerfil} onValueChange={(val) => {
                    setSignupPerfil(val);
                    setSignupArea(val === 'manutencao_eletrica' ? 'Elétrica' : 'Mecânica');
                  }}>
                    <SelectTrigger className="touch-target mt-1"><SelectValue placeholder="Selecione o perfil" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="manutencao_eletrica">Manutenção Elétrica</SelectItem>
                      <SelectItem value="manutencao_mecanica">Manutenção Mecânica</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button type="submit" className="w-full touch-target text-base" disabled={loading}>
                  {loading ? 'Cadastrando...' : 'Cadastrar'}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;

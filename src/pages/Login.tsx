import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Navigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Wrench } from 'lucide-react';
import { toast } from 'sonner';

const Login = () => {
  const { user, signIn } = useAuth();
  const [loading, setLoading] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [keepConnected, setKeepConnected] = useState(true);

  if (user) return <Navigate to="/dashboard" replace />;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await signIn(loginEmail, loginPassword, keepConnected);
      toast.success('Login realizado com sucesso!');
    } catch (err: any) {
      toast.error(err.message || 'Erro ao fazer login');
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
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <Label htmlFor="login-email">Email</Label>
              <Input id="login-email" type="email" value={loginEmail} onChange={e => setLoginEmail(e.target.value)} required className="touch-target mt-1" />
            </div>
            <div>
              <Label htmlFor="login-password">Senha</Label>
              <Input id="login-password" type="password" value={loginPassword} onChange={e => setLoginPassword(e.target.value)} required className="touch-target mt-1" />
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="keep-connected"
                checked={keepConnected}
                onCheckedChange={(checked) => setKeepConnected(checked === true)}
              />
              <Label htmlFor="keep-connected" className="text-sm font-normal cursor-pointer">
                Manter-me conectado
              </Label>
            </div>
            <Button type="submit" className="w-full touch-target text-base" disabled={loading}>
              {loading ? 'Entrando...' : 'Entrar'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;

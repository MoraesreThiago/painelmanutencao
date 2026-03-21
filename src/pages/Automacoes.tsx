
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, FileText, BarChart3, Link2 } from 'lucide-react';

const integrations = [
  {
    title: 'WhatsApp Automático por Turno',
    description: 'Envio automático de resumo das ocorrências do turno via WhatsApp para os supervisores e gestores.',
    icon: MessageSquare,
    status: 'Planejado',
    statusColor: 'bg-status-liberado text-primary-foreground',
  },
  {
    title: 'Resumo Mensal Automático',
    description: 'Geração automática de relatório mensal consolidado com indicadores, gráficos e envio por email.',
    icon: BarChart3,
    status: 'Em estudo',
    statusColor: 'bg-status-andamento text-primary-foreground',
  },
  {
    title: 'Geração Automática de OS',
    description: 'Integração com sistema externo para geração automática de Ordem de Serviço quando marcada na ocorrência.',
    icon: FileText,
    status: 'Planejado',
    statusColor: 'bg-status-liberado text-primary-foreground',
  },
  {
    title: 'Integração com Sistema de Manutenção',
    description: 'Conexão com sistema terceirizado de gestão de manutenção para sincronização de dados e ordens de serviço.',
    icon: Link2,
    status: 'Futuro',
    statusColor: 'bg-muted text-muted-foreground',
  },
];

const Automacoes = () => {
  return (
    <Layout>
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-bold">Automações & Integrações</h1>
          <p className="text-muted-foreground mt-1">Futuras integrações planejadas para o sistema.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {integrations.map(item => (
            <Card key={item.title} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                    <item.icon className="h-6 w-6 text-primary" />
                  </div>
                  <Badge className={item.statusColor}>{item.status}</Badge>
                </div>
                <CardTitle className="text-lg mt-3">{item.title}</CardTitle>
                <CardDescription>{item.description}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    
  );
};

export default Automacoes;

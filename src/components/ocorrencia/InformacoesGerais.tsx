import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { OcorrenciaFormState } from '@/types/ocorrenciaForm';
import type { Tables } from '@/integrations/supabase/types';

type Colaborador = Tables<'colaboradores'>;

interface Props {
  form: OcorrenciaFormState;
  setField: <K extends keyof OcorrenciaFormState>(key: K, value: OcorrenciaFormState[K]) => void;
  colaboradores: Colaborador[];
  isAdmin: boolean;
  profileArea?: string | null;
}

const InformacoesGerais = ({ form, setField, colaboradores, isAdmin, profileArea }: Props) => (
  <Card>
    <CardHeader><CardTitle className="text-base">Informações Gerais</CardTitle></CardHeader>
    <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <Label>Data da Ocorrência *</Label>
        <Input type="date" value={form.data_ocorrencia} onChange={e => setField('data_ocorrencia', e.target.value)} required className="touch-target mt-1" />
      </div>
      <div>
        <Label>Horário *</Label>
        <Select value={form.horario} onValueChange={v => setField('horario', v)}>
          <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="Dia">Dia</SelectItem>
            <SelectItem value="Amanhecida">Amanhecida</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label>Turno *</Label>
        <Select value={form.turno} onValueChange={v => setField('turno', v)}>
          <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
          <SelectContent>
            {['A', 'B', 'C', 'D', 'ADM'].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label>Colaborador *</Label>
        <Select value={form.colaborador_id} onValueChange={v => setField('colaborador_id', v)}>
          <SelectTrigger className="touch-target mt-1"><SelectValue placeholder="Selecione" /></SelectTrigger>
          <SelectContent>
            {colaboradores.filter(c => isAdmin || c.area === profileArea).map(c => (
              <SelectItem key={c.id} value={c.id}>{c.nome} ({c.area})</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label>Status</Label>
        <Select value={form.status} onValueChange={v => setField('status', v)}>
          <SelectTrigger className="touch-target mt-1"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="Pendente">Pendente</SelectItem>
            <SelectItem value="Liberado">Liberado</SelectItem>
            <SelectItem value="Em andamento">Em andamento</SelectItem>
            <SelectItem value="Realizada">Realizada</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label>Área Responsável</Label>
        <Select value={form.area_responsavel} onValueChange={v => setField('area_responsavel', v)}>
          <SelectTrigger className="touch-target mt-1"><SelectValue placeholder="Selecione (opcional)" /></SelectTrigger>
          <SelectContent>
            {(profileArea === 'Elétrica' || isAdmin) && <SelectItem value="Elétrica">Elétrica</SelectItem>}
            {(profileArea === 'Mecânica' || isAdmin) && <SelectItem value="Mecânica">Mecânica</SelectItem>}
            <SelectItem value="Instrumentação">Instrumentação</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardContent>
  </Card>
);

export default InformacoesGerais;

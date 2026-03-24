import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { OcorrenciaFormState } from '@/types/ocorrenciaForm';

interface Props {
  form: OcorrenciaFormState;
  setField: <K extends keyof OcorrenciaFormState>(key: K, value: OcorrenciaFormState[K]) => void;
  profileArea?: string | null;
  isAdmin: boolean;
}

const ParadaSection = ({ form, setField, profileArea, isAdmin }: Props) => (
  <Card>
    <CardHeader><CardTitle className="text-base">Parada</CardTitle></CardHeader>
    <CardContent className="space-y-4">
      <div className="flex items-center gap-3">
        <Switch checked={form.houve_parada} onCheckedChange={v => setField('houve_parada', v)} />
        <Label>Houve parada?</Label>
      </div>
      {form.houve_parada && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <Label>Tipo de Parada</Label>
            <Select value={form.tipo_parada} onValueChange={v => setField('tipo_parada', v)}>
              <SelectTrigger className="touch-target mt-1"><SelectValue placeholder="Selecione" /></SelectTrigger>
              <SelectContent>
                {(profileArea === 'Elétrica' || isAdmin) && <SelectItem value="Elétrica">Elétrica</SelectItem>}
                {(profileArea === 'Elétrica' || profileArea === 'Mecânica' || isAdmin) && <SelectItem value="Instrumentação">Instrumentação</SelectItem>}
                {(profileArea === 'Mecânica' || isAdmin) && <SelectItem value="Mecânica">Mecânica</SelectItem>}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Tempo de Parada (minutos)</Label>
            <Input type="number" value={form.tempo_parada} onChange={e => setField('tempo_parada', e.target.value)} placeholder="Ex: 30" className="touch-target mt-1" />
          </div>
        </div>
      )}
    </CardContent>
  </Card>
);

export default ParadaSection;

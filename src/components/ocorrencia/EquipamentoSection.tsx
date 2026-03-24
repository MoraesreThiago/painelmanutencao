import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { OcorrenciaFormState, EquipamentoView } from '@/types/ocorrenciaForm';

interface Props {
  form: OcorrenciaFormState;
  setField: <K extends keyof OcorrenciaFormState>(key: K, value: OcorrenciaFormState[K]) => void;
  // Tag search
  tagSearch: string;
  onTagSearchChange: (value: string) => void;
  tagSuggestions: EquipamentoView[];
  showTagSuggestions: boolean;
  setShowTagSuggestions: (v: boolean) => void;
  // Eq search
  eqSearch: string;
  onEqSearchChange: (value: string) => void;
  eqSuggestions: EquipamentoView[];
  showEqSuggestions: boolean;
  setShowEqSuggestions: (v: boolean) => void;
  // Local search
  localSearch: string;
  onLocalSearchChange: (value: string) => void;
  localSuggestions: string[];
  showLocalSuggestions: boolean;
  setShowLocalSuggestions: (v: boolean) => void;
  // Select
  onSelectEquipamento: (eq: EquipamentoView) => void;
  onSelectLocal: (loc: string) => void;
}

const EquipamentoSection = ({
  form, setField,
  tagSearch, onTagSearchChange, tagSuggestions, showTagSuggestions, setShowTagSuggestions,
  eqSearch, onEqSearchChange, eqSuggestions, showEqSuggestions, setShowEqSuggestions,
  localSearch, onLocalSearchChange, localSuggestions, showLocalSuggestions, setShowLocalSuggestions,
  onSelectEquipamento, onSelectLocal,
}: Props) => (
  <Card>
    <CardHeader><CardTitle className="text-base">Equipamento</CardTitle></CardHeader>
    <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {/* TAG */}
      <div className="relative">
        <Label>TAG</Label>
        <Input
          value={tagSearch}
          onChange={e => { onTagSearchChange(e.target.value); setField('tag', e.target.value); }}
          onFocus={() => setShowTagSuggestions(true)}
          onBlur={() => setTimeout(() => setShowTagSuggestions(false), 200)}
          placeholder="Digite a TAG"
          className="touch-target mt-1"
        />
        {showTagSuggestions && tagSuggestions.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-card border rounded-md shadow-lg max-h-48 overflow-auto">
            {tagSuggestions.map(eq => (
              <button key={eq.tag} type="button" className="w-full text-left px-3 py-2 hover:bg-muted text-sm" onMouseDown={() => onSelectEquipamento(eq)}>
                <span className="font-medium">{eq.tag}</span> — {eq.equipamento}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Equipamento */}
      <div className="relative">
        <Label>Equipamento</Label>
        <Input
          value={eqSearch}
          onChange={e => { onEqSearchChange(e.target.value); setField('equipamento', e.target.value); }}
          onFocus={() => setShowEqSuggestions(true)}
          onBlur={() => setTimeout(() => setShowEqSuggestions(false), 200)}
          placeholder="Digite o equipamento"
          className="touch-target mt-1"
        />
        {showEqSuggestions && eqSuggestions.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-card border rounded-md shadow-lg max-h-48 overflow-auto">
            {eqSuggestions.map(eq => (
              <button key={eq.tag || eq.equipamento} type="button" className="w-full text-left px-3 py-2 hover:bg-muted text-sm" onMouseDown={() => onSelectEquipamento(eq)}>
                <span className="font-medium">{eq.equipamento}</span>{eq.tag ? ` — ${eq.tag}` : ''}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Local */}
      <div className="relative">
        <Label>Local</Label>
        <Input
          value={localSearch || form.local}
          onChange={e => { onLocalSearchChange(e.target.value); setField('local', e.target.value); }}
          onFocus={() => setShowLocalSuggestions(true)}
          onBlur={() => setTimeout(() => setShowLocalSuggestions(false), 200)}
          placeholder="Digite o local"
          className="touch-target mt-1"
        />
        {showLocalSuggestions && localSearch.length > 0 && localSuggestions.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-card border rounded-md shadow-lg max-h-48 overflow-auto">
            {localSuggestions.map((loc, i) => (
              <button key={i} type="button" className="w-full text-left px-3 py-2 hover:bg-muted text-sm" onMouseDown={() => onSelectLocal(loc)}>
                {loc}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Tipo */}
      <div>
        <Label>Tipo de Ocorrência *</Label>
        <Select value={form.tipo_ocorrencia} onValueChange={v => setField('tipo_ocorrencia', v)}>
          <SelectTrigger className="touch-target mt-1"><SelectValue placeholder="Selecione" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="Corretiva">Corretiva</SelectItem>
            <SelectItem value="Preventiva">Preventiva</SelectItem>
            <SelectItem value="Preditiva">Preditiva</SelectItem>
            <SelectItem value="Inspeção">Inspeção</SelectItem>
            <SelectItem value="Melhoria">Melhoria</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardContent>
  </Card>
);

export default EquipamentoSection;

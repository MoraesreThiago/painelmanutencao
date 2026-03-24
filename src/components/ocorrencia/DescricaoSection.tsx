import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Wand2, Loader2 } from 'lucide-react';

interface Props {
  descricao: string;
  onDescricaoChange: (value: string) => void;
  onImprove: () => void;
  improving: boolean;
}

const DescricaoSection = ({ descricao, onDescricaoChange, onImprove, improving }: Props) => (
  <Card>
    <CardHeader>
      <div className="flex items-center justify-between">
        <CardTitle className="text-base">Descrição</CardTitle>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onImprove}
          disabled={improving || !descricao.trim()}
          className="gap-1.5"
        >
          {improving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
          {improving ? 'Melhorando...' : 'Melhorar com IA'}
        </Button>
      </div>
    </CardHeader>
    <CardContent>
      <Textarea
        value={descricao}
        onChange={e => onDescricaoChange(e.target.value.slice(0, 2000))}
        placeholder="Descreva a ocorrência..."
        rows={4}
        required
        className="touch-target"
        maxLength={2000}
      />
      <p className={`text-xs text-right mt-1 ${descricao.length > 0 && descricao.trim().length < 20 ? 'text-destructive' : 'text-muted-foreground'}`}>
        {descricao.trim().length}/2000 (mín. 20)
      </p>
    </CardContent>
  </Card>
);

export default DescricaoSection;

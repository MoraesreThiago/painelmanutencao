import { Button } from '@/components/ui/button';
import { Save } from 'lucide-react';

interface Props {
  loading: boolean;
  onCancel: () => void;
}

const FormActions = ({ loading, onCancel }: Props) => (
  <div className="flex gap-3 pb-6">
    <Button type="button" variant="outline" onClick={onCancel} className="touch-target flex-1">
      Cancelar
    </Button>
    <Button type="submit" disabled={loading} className="touch-target flex-1">
      <Save className="h-5 w-5 mr-2" /> {loading ? 'Salvando...' : 'Salvar'}
    </Button>
  </div>
);

export default FormActions;

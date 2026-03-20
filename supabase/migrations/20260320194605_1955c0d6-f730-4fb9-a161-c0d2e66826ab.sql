
CREATE TABLE public.motores_eletricos (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  tag text NOT NULL,
  motor text NOT NULL,
  potencia text,
  numero_nf text NOT NULL,
  data_saida date NOT NULL,
  destino text,
  motivo text,
  status_retorno text NOT NULL DEFAULT 'Pendente',
  data_retorno date,
  area text NOT NULL,
  created_by uuid REFERENCES auth.users(id),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

ALTER TABLE public.motores_eletricos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read motores by area"
ON public.motores_eletricos FOR SELECT TO authenticated
USING (has_role(auth.uid(), 'administrador'::app_role) OR area = get_user_area(auth.uid()));

CREATE POLICY "Users can insert motores in their area"
ON public.motores_eletricos FOR INSERT TO authenticated
WITH CHECK (has_role(auth.uid(), 'administrador'::app_role) OR area = get_user_area(auth.uid()));

CREATE POLICY "Users can update motores in their area"
ON public.motores_eletricos FOR UPDATE TO authenticated
USING (has_role(auth.uid(), 'administrador'::app_role) OR area = get_user_area(auth.uid()));

CREATE POLICY "Admins can delete motores"
ON public.motores_eletricos FOR DELETE TO authenticated
USING (has_role(auth.uid(), 'administrador'::app_role));

CREATE TRIGGER set_updated_at_motores
  BEFORE UPDATE ON public.motores_eletricos
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


DROP POLICY IF EXISTS "Users can read ocorrencias by area" ON public.ocorrencias;

CREATE POLICY "Users can read ocorrencias by area"
ON public.ocorrencias
FOR SELECT
TO authenticated
USING (
  has_role(auth.uid(), 'administrador'::app_role)
  OR area = get_user_area(auth.uid())
  OR area_responsavel = get_user_area(auth.uid())
);

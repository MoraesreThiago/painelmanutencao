
-- Restrict colaboradores SELECT to admin or same-area users
DROP POLICY IF EXISTS "Authenticated users can read colaboradores" ON public.colaboradores;

CREATE POLICY "Users can read colaboradores by area"
  ON public.colaboradores
  FOR SELECT
  TO authenticated
  USING (
    has_role(auth.uid(), 'administrador'::app_role)
    OR area = get_user_area(auth.uid())
  );

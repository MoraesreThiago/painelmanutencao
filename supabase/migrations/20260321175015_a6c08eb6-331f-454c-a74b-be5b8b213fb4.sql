
DROP POLICY IF EXISTS "Users can read colaboradores by area" ON public.colaboradores;

CREATE POLICY "Authenticated users can read colaboradores"
ON public.colaboradores
FOR SELECT
TO authenticated
USING (true);

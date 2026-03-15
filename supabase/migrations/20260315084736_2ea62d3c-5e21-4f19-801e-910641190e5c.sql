
-- Remove old permissive INSERT/UPDATE policies on colaboradores
DROP POLICY IF EXISTS "Authenticated can insert colaboradores" ON public.colaboradores;
DROP POLICY IF EXISTS "Authenticated can update colaboradores" ON public.colaboradores;

-- Only admins can insert colaboradores
CREATE POLICY "Admins can insert colaboradores"
  ON public.colaboradores FOR INSERT
  TO authenticated
  WITH CHECK (public.has_role(auth.uid(), 'administrador'));

-- Only admins can update colaboradores
CREATE POLICY "Admins can update colaboradores"
  ON public.colaboradores FOR UPDATE
  TO authenticated
  USING (public.has_role(auth.uid(), 'administrador'));

-- Remove old permissive INSERT/UPDATE policies on equipamentos
DROP POLICY IF EXISTS "Authenticated can insert equipamentos" ON public.equipamentos;
DROP POLICY IF EXISTS "Authenticated can update equipamentos" ON public.equipamentos;

-- Only admins can insert equipamentos
CREATE POLICY "Admins can insert equipamentos"
  ON public.equipamentos FOR INSERT
  TO authenticated
  WITH CHECK (public.has_role(auth.uid(), 'administrador'));

-- Only admins can update equipamentos
CREATE POLICY "Admins can update equipamentos"
  ON public.equipamentos FOR UPDATE
  TO authenticated
  USING (public.has_role(auth.uid(), 'administrador'));

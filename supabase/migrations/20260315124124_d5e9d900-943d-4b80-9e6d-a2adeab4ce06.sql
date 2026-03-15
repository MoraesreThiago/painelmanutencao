
-- Function to get current user's area from profiles
CREATE OR REPLACE FUNCTION public.get_user_area(_user_id uuid)
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT area FROM public.profiles WHERE id = _user_id LIMIT 1;
$$;

-- Drop old SELECT policies
DROP POLICY IF EXISTS "Authenticated can read colaboradores" ON public.colaboradores;
DROP POLICY IF EXISTS "Authenticated can read ocorrencias" ON public.ocorrencias;

-- Colaboradores: admins see all, others see only their area
CREATE POLICY "Users can read colaboradores by area"
ON public.colaboradores FOR SELECT TO authenticated
USING (
  public.has_role(auth.uid(), 'administrador'::app_role)
  OR area = public.get_user_area(auth.uid())
);

-- Ocorrencias: admins see all, others see only their area
CREATE POLICY "Users can read ocorrencias by area"
ON public.ocorrencias FOR SELECT TO authenticated
USING (
  public.has_role(auth.uid(), 'administrador'::app_role)
  OR area = public.get_user_area(auth.uid())
);

-- Also restrict ocorrencias insert/update to user's area (non-admins)
DROP POLICY IF EXISTS "Authenticated can insert ocorrencias" ON public.ocorrencias;
CREATE POLICY "Users can insert ocorrencias in their area"
ON public.ocorrencias FOR INSERT TO authenticated
WITH CHECK (
  public.has_role(auth.uid(), 'administrador'::app_role)
  OR area = public.get_user_area(auth.uid())
);

DROP POLICY IF EXISTS "Authenticated can update ocorrencias" ON public.ocorrencias;
CREATE POLICY "Users can update ocorrencias in their area"
ON public.ocorrencias FOR UPDATE TO authenticated
USING (
  public.has_role(auth.uid(), 'administrador'::app_role)
  OR area = public.get_user_area(auth.uid())
);

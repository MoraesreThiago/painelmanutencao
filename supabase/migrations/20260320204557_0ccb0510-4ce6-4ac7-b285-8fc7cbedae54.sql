-- Helper function to check if user is a leader or supervisor
CREATE OR REPLACE FUNCTION public.is_leader_or_above(_user_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.user_roles
    WHERE user_id = _user_id
      AND role IN ('administrador', 'lider_eletrica', 'lider_mecanica', 'supervisor_eletrica', 'supervisor_mecanica')
  )
$$;

-- Update colaboradores: leaders/supervisors can manage their area
DROP POLICY IF EXISTS "Admins can insert colaboradores" ON public.colaboradores;
CREATE POLICY "Leaders can insert colaboradores"
ON public.colaboradores FOR INSERT TO authenticated
WITH CHECK (
  has_role(auth.uid(), 'administrador'::app_role)
  OR (
    is_leader_or_above(auth.uid())
    AND area = get_user_area(auth.uid())
  )
);

DROP POLICY IF EXISTS "Admins can update colaboradores" ON public.colaboradores;
CREATE POLICY "Leaders can update colaboradores"
ON public.colaboradores FOR UPDATE TO authenticated
USING (
  has_role(auth.uid(), 'administrador'::app_role)
  OR (
    is_leader_or_above(auth.uid())
    AND area = get_user_area(auth.uid())
  )
);

DROP POLICY IF EXISTS "Admins can delete colaboradores" ON public.colaboradores;
CREATE POLICY "Leaders can delete colaboradores"
ON public.colaboradores FOR DELETE TO authenticated
USING (
  has_role(auth.uid(), 'administrador'::app_role)
  OR (
    is_leader_or_above(auth.uid())
    AND area = get_user_area(auth.uid())
  )
);

-- Update ocorrencias: leaders/supervisors can edit without 24h limit
DROP POLICY IF EXISTS "Users can update ocorrencias in their area" ON public.ocorrencias;
CREATE POLICY "Users can update ocorrencias in their area"
ON public.ocorrencias FOR UPDATE TO authenticated
USING (
  has_role(auth.uid(), 'administrador'::app_role)
  OR (
    is_leader_or_above(auth.uid())
    AND area = get_user_area(auth.uid())
  )
  OR (
    area = get_user_area(auth.uid())
    AND created_at > (now() - interval '24 hours')
  )
);

-- Leaders/supervisors can delete ocorrencias in their area
DROP POLICY IF EXISTS "Admins can delete ocorrencias" ON public.ocorrencias;
CREATE POLICY "Leaders can delete ocorrencias"
ON public.ocorrencias FOR DELETE TO authenticated
USING (
  has_role(auth.uid(), 'administrador'::app_role)
  OR (
    is_leader_or_above(auth.uid())
    AND area = get_user_area(auth.uid())
  )
);

-- Update profiles insert policy to allow new role values
DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile"
ON public.profiles FOR INSERT TO authenticated
WITH CHECK (
  id = auth.uid()
  AND perfil = ANY (ARRAY[
    'manutencao_eletrica', 'manutencao_mecanica',
    'lider_eletrica', 'lider_mecanica',
    'supervisor_eletrica', 'supervisor_mecanica'
  ])
);
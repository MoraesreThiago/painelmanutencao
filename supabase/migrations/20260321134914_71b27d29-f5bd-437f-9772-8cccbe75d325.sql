
-- =============================================
-- 1. PROFILES: Replace USING(true) SELECT with area-based access
-- =============================================
-- Admin vê todos; líder/supervisor vê da própria área; usuário comum vê apenas o próprio perfil
DROP POLICY IF EXISTS "Authenticated can read profiles" ON public.profiles;
CREATE POLICY "Users can read profiles by area"
ON public.profiles FOR SELECT TO authenticated
USING (
  has_role(auth.uid(), 'administrador'::app_role)
  OR id = auth.uid()
  OR (
    is_leader_or_above(auth.uid())
    AND area = get_user_area(auth.uid())
  )
);

-- =============================================
-- 2. EQUIPAMENTOS: Replace USING(true) SELECT with area-based access
-- =============================================
-- Admin vê todos; demais vêem apenas da sua área (ou sem área definida)
DROP POLICY IF EXISTS "Authenticated can read equipamentos" ON public.equipamentos;
CREATE POLICY "Users can read equipamentos by area"
ON public.equipamentos FOR SELECT TO authenticated
USING (
  has_role(auth.uid(), 'administrador'::app_role)
  OR area IS NULL
  OR area = get_user_area(auth.uid())
);

-- =============================================
-- 3. OCORRENCIAS_IMPORTACAO: Enable RLS and add admin-only policies
-- =============================================
ALTER TABLE public.ocorrencias_importacao ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admins can select ocorrencias_importacao"
ON public.ocorrencias_importacao FOR SELECT TO authenticated
USING (has_role(auth.uid(), 'administrador'::app_role));

CREATE POLICY "Admins can insert ocorrencias_importacao"
ON public.ocorrencias_importacao FOR INSERT TO authenticated
WITH CHECK (has_role(auth.uid(), 'administrador'::app_role));

CREATE POLICY "Admins can update ocorrencias_importacao"
ON public.ocorrencias_importacao FOR UPDATE TO authenticated
USING (has_role(auth.uid(), 'administrador'::app_role));

CREATE POLICY "Admins can delete ocorrencias_importacao"
ON public.ocorrencias_importacao FOR DELETE TO authenticated
USING (has_role(auth.uid(), 'administrador'::app_role));

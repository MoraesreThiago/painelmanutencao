
-- Fix: restrict profiles INSERT to prevent self-registration as administrator
DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;

CREATE POLICY "Users can insert own profile"
ON public.profiles
FOR INSERT
TO authenticated
WITH CHECK (
  id = auth.uid()
  AND perfil IN ('manutencao_eletrica', 'manutencao_mecanica')
);

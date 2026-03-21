
DROP POLICY "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile" ON public.profiles
  FOR INSERT TO authenticated
  WITH CHECK (
    id = auth.uid()
    AND perfil = ANY (ARRAY[
      'manutencao_eletrica'::text,
      'manutencao_mecanica'::text,
      'manutencao_instrumentacao'::text
    ])
  );

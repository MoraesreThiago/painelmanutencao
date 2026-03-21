DROP POLICY "Users can read equipamentos by area" ON public.equipamentos;
CREATE POLICY "Authenticated users can read equipamentos" ON public.equipamentos
  FOR SELECT TO authenticated
  USING (true);
DROP POLICY "Users can update own profile" ON profiles;
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE TO authenticated
  USING (id = auth.uid())
  WITH CHECK (id = auth.uid() AND perfil = (SELECT p.perfil FROM profiles p WHERE p.id = auth.uid()));
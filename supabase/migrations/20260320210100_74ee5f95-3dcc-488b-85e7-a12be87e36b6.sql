
DROP POLICY IF EXISTS "Admins can delete motores" ON public.motores_eletricos;
CREATE POLICY "Leaders can delete motores"
ON public.motores_eletricos FOR DELETE TO authenticated
USING (
  has_role(auth.uid(), 'administrador'::app_role)
  OR (
    is_leader_or_above(auth.uid())
    AND area = get_user_area(auth.uid())
  )
);

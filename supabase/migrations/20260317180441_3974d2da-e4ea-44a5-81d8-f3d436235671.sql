
-- Drop the existing update policy
DROP POLICY "Users can update ocorrencias in their area" ON public.ocorrencias;

-- Recreate with 24h restriction (admins bypass)
CREATE POLICY "Users can update ocorrencias in their area"
ON public.ocorrencias
FOR UPDATE
TO authenticated
USING (
  has_role(auth.uid(), 'administrador'::app_role)
  OR (
    area = get_user_area(auth.uid())
    AND created_at > (now() - interval '24 hours')
  )
);

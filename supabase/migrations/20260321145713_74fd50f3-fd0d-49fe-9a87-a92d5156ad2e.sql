
CREATE OR REPLACE FUNCTION public.is_leader_or_above(_user_id uuid)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
  SELECT EXISTS (
    SELECT 1 FROM public.user_roles
    WHERE user_id = _user_id
      AND role IN ('administrador', 'lider_eletrica', 'lider_mecanica', 'supervisor_eletrica', 'supervisor_mecanica', 'lider_instrumentacao', 'supervisor_instrumentacao')
  )
$function$;

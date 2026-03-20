-- Add new enum values for leader and supervisor roles
ALTER TYPE public.app_role ADD VALUE IF NOT EXISTS 'lider_eletrica';
ALTER TYPE public.app_role ADD VALUE IF NOT EXISTS 'lider_mecanica';
ALTER TYPE public.app_role ADD VALUE IF NOT EXISTS 'supervisor_eletrica';
ALTER TYPE public.app_role ADD VALUE IF NOT EXISTS 'supervisor_mecanica';
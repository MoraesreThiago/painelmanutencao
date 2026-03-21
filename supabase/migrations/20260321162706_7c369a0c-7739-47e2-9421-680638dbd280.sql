
-- Rename existing 'area' column to 'area_fabrica' on equipamentos
ALTER TABLE public.equipamentos RENAME COLUMN area TO area_fabrica;

-- Add new 'area_manutencao' column for maintenance specialty
ALTER TABLE public.equipamentos ADD COLUMN area_manutencao text;

-- Set area_manutencao default based on existing patterns (can be adjusted later)
-- Default all existing to NULL so admin can classify them

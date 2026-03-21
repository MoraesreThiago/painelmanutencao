
-- Add new roles for Instrumentação
ALTER TYPE app_role ADD VALUE IF NOT EXISTS 'supervisor_instrumentacao';
ALTER TYPE app_role ADD VALUE IF NOT EXISTS 'lider_instrumentacao';
ALTER TYPE app_role ADD VALUE IF NOT EXISTS 'manutencao_instrumentacao';

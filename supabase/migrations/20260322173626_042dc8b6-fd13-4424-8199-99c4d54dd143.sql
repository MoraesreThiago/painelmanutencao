
ALTER TABLE public.motores_eletricos
  ADD COLUMN rpm text NULL,
  ADD COLUMN tensao text NULL,
  ADD COLUMN corrente text NULL,
  ALTER COLUMN data_saida DROP NOT NULL,
  ALTER COLUMN data_saida SET DEFAULT NULL;

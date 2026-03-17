
-- First delete all ocorrencias for Mecânica area
DELETE FROM ocorrencias WHERE area = 'Mecânica';

-- Then delete the test colaboradores
DELETE FROM colaboradores WHERE area = 'Mecânica' AND nome IN (
  'Carlos Silva', 'Roberto Santos', 'Felipe Oliveira', 'Marcos Pereira', 'André Costa'
);

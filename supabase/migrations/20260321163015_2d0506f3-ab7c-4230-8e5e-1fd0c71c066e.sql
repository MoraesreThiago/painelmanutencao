
-- Drop all dependent views cascade
DROP VIEW IF EXISTS public.vw_equipamentos_app CASCADE;
DROP VIEW IF EXISTS public.vw_equipamentos_consolidados CASCADE;
DROP VIEW IF EXISTS public.vw_equipamentos_mapeados CASCADE;

-- Recreate vw_equipamentos_mapeados with area_manutencao
CREATE VIEW public.vw_equipamentos_mapeados WITH (security_invoker = on) AS
WITH base AS (
  SELECT e.id, e.tag, e.equipamento, e.local,
         e.area_fabrica AS area, e.area_manutencao,
         e.status, e.created_at, e.updated_at,
         upper(COALESCE(e.tag, '')) AS tag_u,
         upper(COALESCE(e.local, '')) AS local_u,
         regexp_split_to_array(COALESCE(e.local, ''), '\s/\s') AS partes_local
  FROM equipamentos e
), enriquecido AS (
  SELECT b.*,
    substring(b.tag_u FROM '^([A-Z]{2,4}-[0-9]{4,6}[A-Z]?)$') AS codigo_na_tag,
    substring(b.local_u FROM '([A-Z]{2,4}-[0-9]{4,6}[A-Z]?)') AS codigo_no_local,
    sc.segmento_codigo, sn.segmento_seguinte
  FROM base b
  LEFT JOIN LATERAL (
    SELECT u.seg AS segmento_codigo
    FROM unnest(b.partes_local) WITH ORDINALITY u(seg, ord)
    WHERE upper(u.seg) ~ '[A-Z]{2,4}-[0-9]{4,6}[A-Z]?'
    ORDER BY u.ord LIMIT 1
  ) sc ON true
  LEFT JOIN LATERAL (
    SELECT u2.seg AS segmento_seguinte
    FROM unnest(b.partes_local) WITH ORDINALITY u1(seg, ord)
    JOIN unnest(b.partes_local) WITH ORDINALITY u2(seg, ord) ON u2.ord = (u1.ord + 1)
    WHERE upper(u1.seg) ~ '[A-Z]{2,4}-[0-9]{4,6}[A-Z]?'
    ORDER BY u1.ord LIMIT 1
  ) sn ON true
), mapeado AS (
  SELECT e.*,
    trim(regexp_replace(COALESCE(e.segmento_codigo, ''), '^[A-Z]{2,4}-[0-9]{4,6}[A-Z]?\s*', '')) AS nome_extraido_segmento_codigo
  FROM enriquecido e
)
SELECT id, tag, equipamento, local, area, area_manutencao, status, created_at, updated_at,
  COALESCE(codigo_na_tag, codigo_no_local, tag) AS tag_representacao,
  CASE
    WHEN COALESCE(codigo_na_tag, codigo_no_local) IS NULL THEN equipamento
    WHEN COALESCE(nome_extraido_segmento_codigo, '') <> '' AND upper(nome_extraido_segmento_codigo) <> ALL(ARRAY['CLIMATIZAÇÃO','CLIMATIZACAO','SENSORES','INSTRUMENTOS','VÁLVULAS','VALVULAS']) THEN nome_extraido_segmento_codigo
    WHEN COALESCE(segmento_seguinte, '') <> '' AND upper(segmento_seguinte) <> ALL(ARRAY['CLIMATIZAÇÃO','CLIMATIZACAO','SENSORES','INSTRUMENTOS','VÁLVULAS','VALVULAS']) THEN segmento_seguinte
    ELSE equipamento
  END AS equipamento_representacao,
  CASE WHEN COALESCE(codigo_na_tag, codigo_no_local) IS NOT NULL THEN true ELSE false END AS consolidado_no_pai
FROM mapeado m;

-- Recreate vw_equipamentos_consolidados
CREATE VIEW public.vw_equipamentos_consolidados WITH (security_invoker = on) AS
SELECT
  tag_representacao AS tag,
  equipamento_representacao AS equipamento,
  min(area) AS area,
  min(area_manutencao) AS area_manutencao,
  min(status) AS status,
  min(local) AS local_exemplo,
  max(updated_at) AS updated_at,
  count(*) AS qtd_registros_origem
FROM vw_equipamentos_mapeados
GROUP BY tag_representacao, equipamento_representacao;

-- Recreate vw_equipamentos_app with both area columns
CREATE VIEW public.vw_equipamentos_app WITH (security_invoker = on) AS
SELECT
  tag, equipamento, area AS area_fabrica, area_manutencao, status,
  local_exemplo AS local, updated_at, qtd_registros_origem
FROM vw_equipamentos_consolidados;

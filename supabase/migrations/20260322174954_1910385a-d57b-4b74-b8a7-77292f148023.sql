-- Recreate vw_equipamentos_mapeados with security_invoker = true
CREATE OR REPLACE VIEW public.vw_equipamentos_mapeados
WITH (security_invoker = true)
AS
WITH base AS (
  SELECT e.id, e.tag, e.equipamento, e.local, e.area, e.status, e.created_at, e.updated_at,
         upper(COALESCE(e.tag, ''::text)) AS tag_u,
         upper(COALESCE(e.local, ''::text)) AS local_u,
         regexp_split_to_array(COALESCE(e.local, ''::text), '\s+/\s+'::text) AS partes_local
  FROM equipamentos e
), enriquecido AS (
  SELECT b.*,
         substring(b.tag_u, '^([A-Z]{2,4}-[0-9]{4,6}[A-Z]?)$'::text) AS codigo_na_tag,
         substring(b.local_u, '([A-Z]{2,4}-[0-9]{4,6}[A-Z]?)'::text) AS codigo_no_local,
         sc.segmento_codigo,
         sn.segmento_seguinte
  FROM base b
  LEFT JOIN LATERAL (
    SELECT u.seg AS segmento_codigo
    FROM unnest(b.partes_local) WITH ORDINALITY u(seg, ord)
    WHERE upper(u.seg) ~ '[A-Z]{2,4}-[0-9]{4,6}[A-Z]?'::text
    ORDER BY u.ord LIMIT 1
  ) sc ON true
  LEFT JOIN LATERAL (
    SELECT u2.seg AS segmento_seguinte
    FROM unnest(b.partes_local) WITH ORDINALITY u1(seg, ord)
    JOIN unnest(b.partes_local) WITH ORDINALITY u2(seg, ord) ON u2.ord = u1.ord + 1
    WHERE upper(u1.seg) ~ '[A-Z]{2,4}-[0-9]{4,6}[A-Z]?'::text
    ORDER BY u1.ord LIMIT 1
  ) sn ON true
), mapeado AS (
  SELECT e.*,
         trim(both from regexp_replace(regexp_replace(COALESCE(e.segmento_codigo, ''::text), '^[A-Z]{2,4}-[0-9]{4,6}[A-Z]?\s*[-–—]?\s*'::text, ''::text), '^\s*[-–—]\s*'::text, ''::text)) AS nome_extraido_segmento_codigo
  FROM enriquecido e
)
SELECT id, tag, equipamento, local, area, status, created_at, updated_at,
       COALESCE(codigo_na_tag, codigo_no_local, tag) AS tag_representacao,
       CASE
         WHEN COALESCE(codigo_na_tag, codigo_no_local) IS NULL THEN equipamento
         WHEN COALESCE(nome_extraido_segmento_codigo, ''::text) <> ''::text
              AND upper(nome_extraido_segmento_codigo) <> ALL(ARRAY['CLIMATIZAÇÃO','CLIMATIZACAO','SENSORES','INSTRUMENTOS','VÁLVULAS','VALVULAS'])
              THEN nome_extraido_segmento_codigo
         WHEN COALESCE(segmento_seguinte, ''::text) <> ''::text
              AND upper(segmento_seguinte) <> ALL(ARRAY['CLIMATIZAÇÃO','CLIMATIZACAO','SENSORES','INSTRUMENTOS','VÁLVULAS','VALVULAS'])
              THEN segmento_seguinte
         ELSE equipamento
       END AS equipamento_representacao,
       CASE WHEN COALESCE(codigo_na_tag, codigo_no_local) IS NOT NULL THEN true ELSE false END AS consolidado_no_pai
FROM mapeado m;

-- Recreate vw_equipamentos_app with security_invoker = true
CREATE OR REPLACE VIEW public.vw_equipamentos_app
WITH (security_invoker = true)
AS
SELECT tag_representacao AS tag,
       equipamento_representacao AS equipamento,
       min(area) AS area,
       min(status) AS status,
       min(local) AS local,
       max(updated_at) AS updated_at,
       count(*) AS qtd_registros_origem
FROM vw_equipamentos_mapeados
GROUP BY tag_representacao, equipamento_representacao;
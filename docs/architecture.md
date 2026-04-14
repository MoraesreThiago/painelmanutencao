# Arquitetura Django

## Direção atual

O projeto passou a ter uma espinha dorsal Django em `backend/`, com:

- templates Django como frontend principal
- HTMX para interações incrementais
- DRF para API interna em `/api/v1/`
- apps modulares por domínio
- settings separados por ambiente
- base inicial de PWA com service worker, manifest e fila offline local

## Mapeamento do domínio legado

- `accounts`: usuário, autenticação por e-mail e sessão
- `access`: papéis, permissões, vínculo usuário-área e navegação por contexto
- `unidades`: áreas e localizações
- `colaboradores`: colaboradores operacionais
- `equipamentos`: equipamentos, motores e instrumentos
- `ocorrencias`: movimentações, motores queimados e solicitações de serviço de instrumentos
- `ordens_servico`: ordens externas
- `relatorios`: consolidação mensal via services
- `notificacoes`: eventos de notificação
- `integracoes`: entrada de sincronização/offline outbox
- `auditoria`: trilha de auditoria

## Situação do legado

As pastas `api/` e `web/` ainda permanecem no repositório como referência de migração.
A espinha dorsal nova está em `backend/` e deve concentrar a evolução a partir daqui.

## Próxima fase recomendada

1. portar os demais modelos especializados ainda não migrados
2. trocar os placeholders de navegação por páginas reais por módulo
3. expandir a API v1 com filtros, serializers por domínio e sync mais robusto
4. substituir as integrações legadas restantes pela camada Django

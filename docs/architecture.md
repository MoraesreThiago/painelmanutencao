# Arquitetura Django

## Estado atual

A única stack ativa do projeto está em `backend/`, usando:

- Django como espinha dorsal da aplicação
- Django Templates como frontend principal
- HTMX para interações incrementais
- Django REST Framework para a API interna em `/api/v1/`
- apps modulares por domínio
- base inicial de PWA com `manifest`, `service worker` e fila offline/outbox

A stack anterior em FastAPI/Reflex foi removida do repositório. Novas evoluções devem acontecer somente em `backend/`.

## Apps Django ativos

- `common`: componentes transversais. Contém modelos base com UUID/timestamps, middleware de contexto assumido, permissões globais, context processor do shell, views de home/offline/PWA e comandos compartilhados como `bootstrap_system`.
- `accounts`: autenticação e usuário customizado. Contém o modelo `User`, manager, formulários e views de login/logout.
- `access`: controle de acesso e navegação. Contém `Role`, `UserArea`, formulários e mixins de contexto, dashboard, troca de contexto por área/papel, resumo mensal e a tela de monitoramento de energia.
- `assistente`: chat operacional com IA. Contém `ChatSession`, `ChatMessage`, views/templates do chat e services que montam contexto de ocorrências e chamam a OpenAI quando configurada.
- `unidades`: estrutura física e escopo organizacional. Contém `Area`, `Fabrica`, `UnidadeProdutiva`, `Location`, services de visibilidade/escopo e comando de seed para fábricas e unidades.
- `colaboradores`: gestão de equipe operacional. Contém o modelo `Collaborator`, filtros, paginação, escopo por área/unidade e a listagem da equipe.
- `equipamentos`: ativos base do sistema. Contém `Equipment`, `Motor`, `Instrument`, formulários, serializers, CRUD web/API, filtros, paginação e alternância de status.
- `motores`: catálogo técnico de motores e fluxo principal de motores queimados. Contém `ElectricMotor`, `BurnedMotorCase`, `BurnedMotorCaseEvent`, formulários, views, services, timeline e envio de e-mail para PCM.
- `ocorrencias`: fluxo de ocorrências operacionais. Contém `Occurrence`, `Movement`, `InstrumentServiceRequest`, histórico/timeline, CRUD web/API e sincronização do status operacional dos equipamentos. Também mantém o modelo legado `BurnedMotorRecord`, mas o fluxo ativo de motores queimados fica em `motores`.
- `ordens_servico`: ordens de serviço externas. Contém `ExternalServiceOrder`, filtros, listagem e detalhe.
- `relatorios`: camada de consolidação. Hoje contém principalmente services para resumo mensal e agregações usadas pelo módulo de acesso.
- `notificacoes`: eventos de notificação. Contém o modelo `NotificationEvent` e services básicos para filas pendentes.
- `integracoes`: sincronização e suporte offline. Contém `SyncOutboxEntry` e services para enfileirar e marcar itens sincronizados.
- `auditoria`: trilha de auditoria. Contém `AuditLog` e services para registrar e consultar eventos de auditoria.

## API interna

A API ativa do Django fica em `backend/api/v1/` e hoje expõe principalmente:

- autenticação por sessão (`login`, `logout`, `me`)
- dashboard
- equipamentos
- ocorrências
- recepção de itens para `sync/outbox`

## Modelos importantes

| Conceito | Modelo correto | App |
|---|---|---|
| Motor como subtipo de equipamento | `Motor` | `apps.equipamentos` |
| Motor elétrico do catálogo técnico | `ElectricMotor` | `apps.motores` |
| Processo de motor queimado | `BurnedMotorCase` | `apps.motores` |
| Evento de timeline de motor queimado | `BurnedMotorCaseEvent` | `apps.motores` |
| Equipamento genérico | `Equipment` | `apps.equipamentos` |
| Instrumento | `Instrument` | `apps.equipamentos` |

## Modelos depreciados

- `motores.BurnedMotorProcess` está depreciado e não deve ser usado em código novo. O fluxo ativo e a modelagem correta de motores queimados estão em `BurnedMotorCase`.

## Problema conhecido em aberto

Há hoje duas entidades de motor no backend ativo:

- `ordens_servico.ExternalServiceOrder` aponta para `equipamentos.Motor`
- `motores.BurnedMotorCase` aponta para `motores.ElectricMotor`

Esses dois modelos não têm chave estrangeira entre si. Esse conflito de modelagem está documentado e ainda precisa de uma resolução explícita antes de novas expansões nessa área.

## Regras de organização

- regras de negócio devem ficar em `services.py` de cada app
- views devem permanecer enxutas, sem concentrar lógica de negócio
- permissões centrais ficam em `common/permissions.py`
- código novo não deve recriar dependências diretas da stack legada removida

## Próxima fase recomendada

1. resolver o conflito entre `equipamentos.Motor` e `motores.ElectricMotor`
2. portar os demais modelos especializados ainda não migrados
3. trocar os placeholders de navegação por páginas reais por módulo
4. expandir a API v1 com filtros, serializers por domínio e sync mais robusto
5. substituir as integrações legadas restantes pela camada Django

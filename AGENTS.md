---
# Guia para agentes de IA — PainelManutenção

## Stack ativa
A única stack ativa é `backend/` (Django + DRF + HTMX).
As stacks antigas em FastAPI e Reflex foram removidas do repositório — NÃO recrie nem edite código novo nelas.

## Mapa de modelos importantes

| Conceito | Modelo correto | App |
|---|---|---|
| Motor como subtipo de equipamento | `Motor` | `apps.equipamentos` |
| Motor elétrico do catálogo técnico | `ElectricMotor` | `apps.motores` |
| Processo de motor queimado | `BurnedMotorCase` | `apps.motores` |
| Evento de timeline de motor queimado | `BurnedMotorCaseEvent` | `apps.motores` |
| Equipamento genérico | `Equipment` | `apps.equipamentos` |
| Instrumento | `Instrument` | `apps.equipamentos` |

## Modelos depreciados (não usar em código novo)
- `motores.BurnedMotorProcess` — será removido. Use `BurnedMotorCase`.
- `backend/apps/motores/migrations/0001_initial.py` linha 46 — migration inicial cria o modelo `BurnedMotorProcess`
- `backend/apps/motores/migrations/0001_initial.py` linha 84 — migration inicial referencia `burnedmotorprocess` em operação de campo relacional
- `backend/apps/motores/migrations/0001_initial.py` linha 88 — migration inicial referencia `burnedmotorprocess` em operação de campo relacional

## Ponte entre os dois Motores
`equipamentos.Motor` agora tem FK opcional `electric_motor` para
`motores.ElectricMotor`. A ligação não é automática — deve ser preenchida
ao cadastrar ou editar um Motor em equipamentos quando o motor elétrico
do catálogo for conhecido.
`ordens_servico.ExternalServiceOrder` continua apontando para
`equipamentos.Motor` (sem mudança). Para chegar ao BurnedMotorCase
a partir de uma OS: `service_order.motor.electric_motor.burned_cases`.

## Regras gerais
- Regras de negócio ficam em `services.py` de cada app.
- Views ficam enxutas — sem lógica de negócio.
- Permissões ficam em `common/permissions.py`.
- Nunca recrie dependências diretas da stack legada removida.
---

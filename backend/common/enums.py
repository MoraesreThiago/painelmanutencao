from django.db import models


class RoleName(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    GERENTE = "GERENTE", "Gerente"
    SUPERVISOR = "SUPERVISOR", "Supervisor"
    LIDER = "LIDER", "Líder"
    INSPETOR = "INSPETOR", "Inspetor"
    MANUTENTOR = "MANUTENTOR", "Manutentor"


class AreaCode(models.TextChoices):
    ELETRICA = "ELETRICA", "Elétrica"
    MECANICA = "MECANICA", "Mecânica"
    INSTRUMENTACAO = "INSTRUMENTACAO", "Instrumentação"


class RecordStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Ativo"
    INACTIVE = "INACTIVE", "Inativo"


class EquipmentType(models.TextChoices):
    GENERIC = "GENERIC", "Genérico"
    MOTOR = "MOTOR", "Motor"
    INSTRUMENT = "INSTRUMENT", "Instrumento"


class EquipmentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Ativo"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE", "Em manutenção"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE", "Serviço externo"
    INACTIVE = "INACTIVE", "Inativo"


class OccurrenceClassification(models.TextChoices):
    FAILURE = "FAILURE", "Falha"
    ANOMALY = "ANOMALY", "Anomalia"
    INSPECTION = "INSPECTION", "Inspecao"
    PREVENTIVE = "PREVENTIVE", "Preventiva"
    OTHER = "OTHER", "Outro"


class OccurrenceStatus(models.TextChoices):
    OPEN = "OPEN", "Aberta"
    IN_PROGRESS = "IN_PROGRESS", "Em andamento"
    WAITING_PARTS = "WAITING_PARTS", "Aguardando recurso"
    RESOLVED = "RESOLVED", "Resolvida"
    CANCELLED = "CANCELLED", "Cancelada"


class MotorStatus(models.TextChoices):
    IN_OPERATION = "IN_OPERATION", "Em operação"
    RESERVE = "RESERVE", "Reserva"
    INTERNAL_MAINTENANCE = "INTERNAL_MAINTENANCE", "Manutenção interna"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE", "Serviço externo"
    AWAITING_INSTALLATION = "AWAITING_INSTALLATION", "Aguardando instalação"
    INACTIVE = "INACTIVE", "Inativo"


class InstrumentStatus(models.TextChoices):
    INSTALLED = "INSTALLED", "Instalado"
    IN_STOCK = "IN_STOCK", "Em estoque"
    IN_CALIBRATION = "IN_CALIBRATION", "Em calibração"
    IN_MAINTENANCE = "IN_MAINTENANCE", "Em manutenção"
    AWAITING_INSTALLATION = "AWAITING_INSTALLATION", "Aguardando instalação"
    INACTIVE = "INACTIVE", "Inativo"


class ExternalServiceStatus(models.TextChoices):
    OPEN = "OPEN", "Aberta"
    IN_PROGRESS = "IN_PROGRESS", "Em andamento"
    RETURNED = "RETURNED", "Retornada"
    DELAYED = "DELAYED", "Atrasada"
    CANCELLED = "CANCELLED", "Cancelada"


class BurnedMotorStatus(models.TextChoices):
    OPEN = "OPEN", "Aberto"
    UNDER_ANALYSIS = "UNDER_ANALYSIS", "Em análise"
    SENT_TO_REPAIR = "SENT_TO_REPAIR", "Enviado para reparo"
    REPAIRED = "REPAIRED", "Reparado"
    DISCARDED = "DISCARDED", "Descartado"


class MotorBurnoutFlowStatus(models.TextChoices):
    REGISTERED = "REGISTERED", "Registrado"
    AWAITING_PCM = "AWAITING_PCM", "Aguardando envio para PCM"
    PCM_ANALYSIS = "PCM_ANALYSIS", "Em analise no PCM"
    IN_QUOTATION = "IN_QUOTATION", "Em cotacao"
    AWAITING_APPROVAL = "AWAITING_APPROVAL", "Aguardando aprovacao"
    PAYMENT_APPROVED = "PAYMENT_APPROVED", "Pagamento aprovado"
    IN_REWINDING = "IN_REWINDING", "Em rebobinamento"
    IN_TRANSPORT = "IN_TRANSPORT", "Em transporte"
    RECEIVED = "RECEIVED", "Recebido"
    COMPLETED = "COMPLETED", "Concluido"


class BurnedMotorCaseStatus(models.TextChoices):
    OPEN = "OPEN", "Aberto"
    IDENTIFIED = "IDENTIFIED", "Identificado na oficina"
    AWAITING_PCM = "AWAITING_PCM", "Aguardando envio ao PCM"
    SENT_TO_PCM = "SENT_TO_PCM", "Enviado ao PCM"
    PCM_ANALYSIS = "PCM_ANALYSIS", "Em analise no PCM"
    SENT_TO_FINANCE = "SENT_TO_FINANCE", "Enviado ao financeiro"
    AWAITING_APPROVAL = "AWAITING_APPROVAL", "Aguardando aprovacao"
    APPROVED = "APPROVED", "Aprovado"
    AWAITING_VENDOR = "AWAITING_VENDOR", "Aguardando empresa terceira"
    AWAITING_FREIGHT = "AWAITING_FREIGHT", "Aguardando coleta/frete"
    IN_TRANSPORT = "IN_TRANSPORT", "Em transporte"
    IN_REWINDING = "IN_REWINDING", "Em rebobinamento"
    AWAITING_RETURN = "AWAITING_RETURN", "Aguardando retorno"
    RECEIVED = "RECEIVED", "Recebido"
    COMPLETED = "COMPLETED", "Concluido"
    CANCELLED = "CANCELLED", "Cancelado"


class BurnedMotorPriority(models.TextChoices):
    LOW = "LOW", "Baixa"
    MEDIUM = "MEDIUM", "Media"
    HIGH = "HIGH", "Alta"
    CRITICAL = "CRITICAL", "Critica"


class MotorSolutionType(models.TextChoices):
    UNDER_EVALUATION = "UNDER_EVALUATION", "Em avaliacao"
    NEW_PURCHASE = "NEW_PURCHASE", "Compra de motor novo"
    REWINDING = "REWINDING", "Rebobinamento"
    INTERNAL_REPAIR = "INTERNAL_REPAIR", "Reparo interno"
    THIRD_PARTY_REPAIR = "THIRD_PARTY_REPAIR", "Reparo terceirizado"
    SCRAP = "SCRAP", "Sucateamento"


class MotorDataOrigin(models.TextChoices):
    CATALOG = "CATALOG", "Cadastro existente"
    MANUAL = "MANUAL", "Informado manualmente"
    PROVISIONAL = "PROVISIONAL", "Cadastro provisório"


class InstrumentServiceType(models.TextChoices):
    MAINTENANCE = "MAINTENANCE", "Manutenção"
    CALIBRATION = "CALIBRATION", "Calibração"
    THIRD_PARTY_REPAIR = "THIRD_PARTY_REPAIR", "Reparo terceirizado"


class InstrumentServiceStatus(models.TextChoices):
    OPEN = "OPEN", "Aberto"
    IN_PROGRESS = "IN_PROGRESS", "Em andamento"
    SENT_TO_VENDOR = "SENT_TO_VENDOR", "Enviado ao fornecedor"
    COMPLETED = "COMPLETED", "Concluído"
    CANCELLED = "CANCELLED", "Cancelado"


class NotificationStatus(models.TextChoices):
    PENDING = "PENDING", "Pendente"
    PROCESSED = "PROCESSED", "Processado"
    ERROR = "ERROR", "Erro"

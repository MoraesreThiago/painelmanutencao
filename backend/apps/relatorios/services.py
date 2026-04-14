from django.db.models import Count

from apps.equipamentos.models import Equipment
from apps.ordens_servico.models import ExternalServiceOrder


def monthly_summary(area=None):
    equipments = Equipment.objects.all()
    service_orders = ExternalServiceOrder.objects.all()
    if area is not None:
        equipments = equipments.filter(area=area)
        service_orders = service_orders.filter(motor__equipment__area=area)
    return {
        "equipment_total": equipments.count(),
        "external_service_total": service_orders.count(),
        "equipment_by_type": list(equipments.values("type").annotate(total=Count("id")).order_by("type")),
    }
